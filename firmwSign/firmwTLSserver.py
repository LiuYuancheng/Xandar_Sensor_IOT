#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        TLS_sslSErver.py
#
# Purpose:     This module is used to create a SSL server.   
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

LOCAL_PORT = 5005 # Server defualt listening port.
LISTEN_NUM = 1 # how many client we can handle at same time.
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class TLS_sslServer(object):
    """ Create a SSL client."""

    def __init__(self, parent):
        """ Load the certificate + pricate key file and init the ssl server.
        """
        self.parent = parent
        self.cli = None  # the send()/recv() client we need to return.
        self.server = None
        # Initialize context
        self.ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.ctx.set_options(SSL.OP_NO_SSLv2)
        self.ctx.set_options(SSL.OP_NO_SSLv3)
        self.ctx.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.verify_cb
        )  # Demand a certificate
        self.ctx.use_privatekey_file(gv.SSSL_PRIK_PATH)
        self.ctx.use_certificate_file(gv.SSSL_CERT_PATH)
        self.ctx.load_verify_locations(gv.CA_PATH)

#-----------------------------------------------------------------------------
    def accept(self):
        """ return the SSL.Connection.accept() data.
            usage example: conn, addr = self.tcpServer.accept()
        """
        return self.server.accept()

#-----------------------------------------------------------------------------
    def acceptConnection(self):
        """ If the user don't want to expose SSL.Connection.accept() data.
        """
        self.cli, addr = self.server.accept()
        print('Connection from %s' % (addr,))
        
#-----------------------------------------------------------------------------
    def close(self):
        """Close the server."""
        if not self.cli: self.cli.close()
        self.server.close()

#-----------------------------------------------------------------------------
    def serverSet(self, port=LOCAL_PORT, listen=LISTEN_NUM, block=1):
        """ Set up the SSL server. 
        """
        self.server = SSL.Connection(self.ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.server.bind(('', int(port)))
        self.server.listen(listen)
        self.server.setblocking(block)

#-----------------------------------------------------------------------------
    def verify_cb(self, conn, cert, errnum, depth, ok):
        """ Verifiy the cerificate from client side."""
        certsubject = crypto.X509Name(cert.get_subject())
        commonname = certsubject.commonName
        print('Got certificate: ' + commonname)
        return ok

#-----------------------------------------------------------------------------
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
            pass
        except SSL.Error as errors:
            pass

#-----------------------------------------------------------------------------
    def send(self, data):
        if not isinstance(data, bytes):
            print("The send data must be bytes format.")
            return None
        self.cli.send(data)

#-----------------------------------------------------------------------------
    def shutdown(self):
        if not self.cli:
            self.cli.shutdown()
        self.server.shutdown()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase():
    print("Stepup server test")
    sslServer = TLS_sslServer(None)
    sslServer.serverSet(port=5005, listen=1, block=1)
    print("accept the connection from the client")

    while 1:
        sslServer.acceptConnection()
        while 1:
            data = sslServer.recv(1024)
            if data is not None:
                print(str(data))
            if data is not None:
                sslServer.send(b"server test string")
            if data is None:
                break

    print("Finished and stop")
    sslServer.shutdown()
    sslServer.close()


if __name__ == '__main__':
    pass
    testCase()
