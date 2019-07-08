#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        TLS_sslSErver.py
#
# Purpose:     This module is used to create a SSL server for the Transport Layer 
#              Security communication.
#
# Author:      Yuancheng Liu
#
# Created:     2019/05/13
# Copyright:   NUS – Singtel Cyber Security Research & Development Laboratory
# License:     YC @ NUS
#-----------------------------------------------------------------------------
import os
import sys
import socket
from OpenSSL import SSL, crypto
import firmwGlobal as gv

LOCAL_PORT = 5005   # Server defualt listening port.
LISTEN_NUM = 1      # how many clients we can handle at same time.

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class TLS_sslServer(object):
    """ Create a SSL server."""
    def __init__(self, parent):
        """ Load the CA + certificate + pricate key and init the SSL server."""
        self.parent = parent
        self.cli = None  # the send()/recv() client we need to return.
        self.server = None
        # Initialize context
        self.ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.ctx.set_options(SSL.OP_NO_SSLv2)
        self.ctx.set_options(SSL.OP_NO_SSLv3)
        # Demand a certificate
        self.ctx.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self._verifyCert)  
        self.ctx.use_privatekey_file(gv.SSSL_PRIK_PATH)
        self.ctx.use_certificate_file(gv.SSSL_CERT_PATH)
        self.ctx.load_verify_locations(gv.CA_PATH)

#--TLS_sslServer---------------------------------------------------------------
    def accept(self):
        """ return the SSL.Connection.accept() data.
            usage example: conn, addr = self.tcpServer.accept()
        """
        return self.server.accept()

#--TLS_sslServer---------------------------------------------------------------
    def acceptConnection(self):
        """ If the user don't want to expose SSL.Connection.accept() data."""
        self.cli, addr = self.server.accept()
        print('Connection from %s' % (addr,))
        
#--TLS_sslServer---------------------------------------------------------------
    def close(self):
        """Close the server."""
        if not self.cli: self.cli.close()
        self.server.close()

#--TLS_sslServer---------------------------------------------------------------
    def serverSet(self, port=LOCAL_PORT, listen=LISTEN_NUM, block=1):
        """ Set up the SSL server. """
        self.server = SSL.Connection(self.ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.server.bind(('', int(port)))
        self.server.listen(listen)
        self.server.setblocking(block)

#--TLS_sslServer---------------------------------------------------------------
    def _verifyCert(self, conn, cert, errnum, depth, ok):
        """ Verifiy the cerificate from client side."""
        certsubject = crypto.X509Name(cert.get_subject())
        commonname = certsubject.commonName
        print('Got certificate: ' + commonname)
        return ok

#--TLS_sslServer---------------------------------------------------------------
    def recv(self, buffSZ):
        """ recieve data from the client."""
        try:
            data = self.cli.recv(buffSZ)
            return data
        except (SSL.WantReadError,
                SSL.WantWriteError,
                SSL.WantX509LookupError):
            pass
        except SSL.ZeroReturnError:
            # The server has disconnected.
            self.cli.shutdown()
        except SSL.Error as errors:
            print("Error: SSL error. ")

#--TLS_sslServer---------------------------------------------------------------
    def send(self, data):
        """ Send data to server, will convert not bytes type data to bytes 
            by using utf-8 encoding.
        """
        if not isinstance(data, bytes):
            print("The send data <%s> has been converted to bytes format." %str(data))
            data = str(data).encode('utf-8')
        self.cli.send(data)

#--TLS_sslServer---------------------------------------------------------------
    def shutdown(self):
        if self.cli: self.cli.shutdown()
        if self.server: self.server.shutdown()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase():
    print("Set up server test.")
    sslServer = TLS_sslServer(None)
    sslServer.serverSet(port=LOCAL_PORT, listen=1, block=1)
    print("Accept the connection from the client")

    while 1:
        sslServer.acceptConnection()
        while 1:
            data = sslServer.recv(1024)
            if data is not None:
                print(str(data))
                sslServer.send(b"server test string")
            if data is None:
                break

    print("Finished and stop")
    sslServer.shutdown()
    sslServer.close()

if __name__ == '__main__':
    pass
    testCase()
