#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        TLS_sslClient.py
#
# Author:      Yuancheng Liu
#
# Created:     2019/05/13
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------
import os
import socket
import sys
from OpenSSL import SSL, crypto

dirpath = os.getcwd()
print("Current working directory is : %s" %dirpath)
CA_PATH = "".join([dirpath, "\\firmwSign\\testCert\\CA.cert"])
PRIK_PATH = "".join([dirpath, "\\firmwSign\\testCert\\client.pkey"])
CERT_PATH = "".join([dirpath, "\\firmwSign\\testCert\\client.cert"])
# Set up client
LOCAL_IP = ("127.0.0.1", 5005)

class TLS_sslClient(object):
    """ firmware Sign system dataBase manager. 
    """
    def __init__(self, parent):
        self.parent = parent
        # Initialize context
        self.ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.ctx.set_options(SSL.OP_NO_SSLv2)
        self.ctx.set_options(SSL.OP_NO_SSLv3)
        self.ctx.set_verify(SSL.VERIFY_PEER, self.verify_cb)  # Demand a certificate
        self.ctx.use_privatekey_file(PRIK_PATH)
        self.ctx.use_certificate_file(CERT_PATH)
        self.ctx.load_verify_locations(CA_PATH)

    def verify_cb(self, conn, cert, errnum, depth, ok):
        certsubject = crypto.X509Name(cert.get_subject())
        commonname = certsubject.commonName
        print('Got certificate: ' + commonname)
        return ok

    def connect(self, ipaddr):
        ip, port = ipaddr
        self.sock = SSL.Connection(self.ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.sock.connect((ip, int(port)))

    def send(self, data):
        if not isinstance(data, bytes):
            print("The send data must be bytes format.")
            return None
        self.sock.send(data)

    def recv(self, buffSZ=4096):
        return self.sock.recv(buffSZ)

    def shutdown(self):
        return self.sock.shutdown()

    def close(self):
        return self.sock.close()

def testCase():
    print("connect to server test")
    sslClient = TLS_sslClient(None)
    sslClient.connect(LOCAL_IP)
    print("send the message to server")
    for _ in range(6):
        sslClient.send(b"test string")
        print(sslClient.recv(buffSZ=1024).decode('utf-8'))
    print("Finished and stop")
    sslClient.shutdown()
    sslClient.close()

if __name__ == '__main__':
    pass
    testCase()
