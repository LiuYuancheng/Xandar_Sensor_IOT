#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        TLS_sslClient.py
#
# Purpose:     This module is used to create a SSL client.   
#
# Author:      Yuancheng Liu
#
# Created:     2019/05/13
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------

import os
import sys
import socket
from OpenSSL import SSL, crypto
import firmwGlobal as gv

# Use Local IP and port 5005 as defualt value for test.
LOCAL_IP = ("127.0.0.1", 5005)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class TLS_sslClient(object):
    """ Create a SSL client."""
    def __init__(self, parent):
        """ Load the CA + certifcate + private key and init the SSL client. """
        self.parent = parent
        # Initialize certifcate context
        self.ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.ctx.set_options(SSL.OP_NO_SSLv2)
        self.ctx.set_options(SSL.OP_NO_SSLv3)
        # Demand a certificate
        self.ctx.set_verify(SSL.VERIFY_PEER, self.verifyCert)
        # load the certifcate fils.
        self.ctx.use_privatekey_file(gv.CSSL_PRIK_PATH)
        self.ctx.use_certificate_file(gv.CSSL_CERT_PATH)
        self.ctx.load_verify_locations(gv.CA_PATH)

#-----------------------------------------------------------------------------
    def connect(self, ipaddr):
        """ Init the SSL socket to connect to the server.
            ipaddr = (str(ip), int(port))
        """
        ip, port = ipaddr
        self.sock = SSL.Connection(self.ctx, socket.socket(
            socket.AF_INET, socket.SOCK_STREAM))
        self.sock.connect((ip, int(port)))

    def close(self):
        return self.sock.close()

#-----------------------------------------------------------------------------
    def recv(self, buffSZ):
        return self.sock.recv(buffSZ)

#-----------------------------------------------------------------------------
    def send(self, data):
        """ Send data to server, will convert not bytes type data to bytes 
            by using utf-8 encoding.
        """
        if not isinstance(data, bytes):
            print("The send data <%s> has been converted to bytes format." %str(data))
            data = str(data).encode('utf-8')
        self.sock.send(data)

#-----------------------------------------------------------------------------
    def shutdown(self):
        return self.sock.shutdown()

#-----------------------------------------------------------------------------
    def verifyCert(self, conn, cert, errnum, depth, ok):
        """ Verifiy the cerificate from server side."""
        certsubject = crypto.X509Name(cert.get_subject())
        commonname = certsubject.commonName
        print('Got certificate: ' + commonname)
        return ok

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def testCase():
    print("SSL Connect to server test:")
    sslClient = TLS_sslClient(None)
    sslClient.connect(LOCAL_IP)
    print("Send the message to server")
    for _ in range(6):
        sslClient.send(b"send test string")
        print(sslClient.recv(gv.BUFFER_SIZE).decode('utf-8'))
    print("Finished and stop")
    sslClient.shutdown()
    sslClient.close()

if __name__ == '__main__':
    pass
    testCase()
