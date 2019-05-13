#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        TLS_sslSErver.py
#
# Author:      Yuancheng Liu
#
# Created:     2019/05/13
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------
import os
import select
import socket
import sys

from OpenSSL import SSL, crypto

dirpath = os.getcwd()
print("Current working directory is : %s" %dirpath)
CA_PATH = "".join([dirpath, "\\testCert\\CA.cert"])
PRIK_PATH = "".join([dirpath, "\\testCert\\server.pkey"])
CERT_PATH = "".join([dirpath, "\\testCert\\server.cert"])
LOCAL_PORT = 5005
LISTEN_NUM = 1

class TLS_sslServer(object):
    """ firmware Sign system dataBase manager. 
    """
    def __init__(self, parent):
        self.parent = parent
        self.cli = None
        # Initialize context
        self.ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.ctx.set_options(SSL.OP_NO_SSLv2)
        self.ctx.set_options(SSL.OP_NO_SSLv3)
        self.ctx.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.verify_cb
        )  # Demand a certificate
        self.ctx.use_privatekey_file(PRIK_PATH)
        self.ctx.use_certificate_file(CERT_PATH)
        self.ctx.load_verify_locations(CA_PATH)

    def verify_cb(self, conn, cert, errnum, depth, ok):
        certsubject = crypto.X509Name(cert.get_subject())
        commonname = certsubject.commonName
        print('Got certificate: ' + commonname)
        return ok

    def serverSet(self, port=LOCAL_PORT, listen=LISTEN_NUM, block=1):
        self.server = SSL.Connection(self.ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.server.bind(('', int(port)))
        self.server.listen(listen)
        self.server.setblocking(block)

    def acceptConnection(self):
        self.cli, addr = self.server.accept()
        print('Connection from %s' % (addr,))

    def recv(self, buffSZ):
        try:
            data = self.cli.recv(buffSZ)
            return data
        except (SSL.WantReadError,
            SSL.WantWriteError,
            SSL.WantX509LookupError):
            pass
        except SSL.ZeroReturnError:
            print
            self.cli.shutdown()
            pass
        except SSL.Error as errors:
            pass

    def send(self, data):
        if not isinstance(data, bytes):
            print("The send data must be bytes format.")
            return None
        self.cli.send(data)

    def shutdown(self):
        if not self.cli:
            self.cli.shutdown()
        self.server.shutdown()

    def close(self):
        if not self.cli:
            self.cli.close()
        self.server.close()

def testCase():
    print("Stepup server test")
    sslServer = TLS_sslServer(None)
    sslServer.serverSet(port = 5005, listen=1, block=1 )
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


# clients = {}
# writers = {}


# def dropClient(cli, errors=None):
#     if errors:
#         print('Client %s left unexpectedly:' % (clients[cli],))
#         print('  ', errors)
#     else:
#         print('Client %s left politely' % (clients[cli],))
#     del clients[cli]
#     if cli in writers:
#         del writers[cli]
#     if not errors:
#         cli.shutdown()
#     cli.close()

# while 1:
#     try:
#         r, w, _ = select.select(
#             [server] + list(clients.keys()), list(writers.keys()), []
#         )
#     except Exception:
#         break

#     for cli in r:
#         if cli == server:
#             cli, addr = server.accept()
#             print('Connection from %s' % (addr,))
#             clients[cli] = addr

#         else:
#             try:
#                 ret = cli.recv(1024).decode('utf-8')
#             except (SSL.WantReadError,
#                     SSL.WantWriteError,
#                     SSL.WantX509LookupError):
#                 pass
#             except SSL.ZeroReturnError:
#                 dropClient(cli)
#             except SSL.Error as errors:
#                 dropClient(cli, errors)
#             else:
#                 if cli not in writers:
#                     writers[cli] = ''
#                 writers[cli] = writers[cli] + ret

#     for cli in w:
#         try:
#             ret = cli.send(b"456456")
#         except (SSL.WantReadError,
#                 SSL.WantWriteError,
#                 SSL.WantX509LookupError):
#             pass
#         except SSL.ZeroReturnError:
#             dropClient(cli)
#         except SSL.Error as errors:
#             dropClient(cli, errors)
#         else:
#             writers[cli] = writers[cli][ret:]
#             if writers[cli] == '':
#                 del writers[cli]

# for cli in clients.keys():
#     cli.close()
# server.close()