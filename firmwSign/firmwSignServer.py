#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        firmwareSignServer.py
#
# Purpose:     This module is used to connect to the firmware sign client and:
#               - Check the certificate fetch request valid
#               - Send the certificate file and decrypt the message. 
# Author:      Yuancheng Liu
#
# Created:     2019/04/29
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------
import os
import sys
import json
import socket
import chilkat

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response


dirpath = os.getcwd()
print("current directory is : " + dirpath)

CERT_PATH = "".join([dirpath, "\\publickey.cer"])
PRI_PATH = "".join( [dirpath, "\\privatekey.pem"])
ENCODE_MODE = 'hex'
# create the decoder

class FirmwServ(object):
    
    def __init__(self):

        self.rsaDecryptor = self.initDecoder(Mode='RSA')
        self.tcpServer = self.initTCPServ()

    def initDecoder(self, Mode=None):
        if not Mode:
            print("Decode mode missing.")
            return None
        elif Mode == 'RSA':
            rsaDecryptor = chilkat.CkRsa()
            if not rsaDecryptor.UnlockComponent("Anything for 30-day trial"):
                print("RSA component unlock failed")
                sys.exit()
            privKey = chilkat.CkPrivateKey()
            success = privKey.LoadPemFile(PRI_PATH)
            if not success:
                print(privKey.lastErrorText())
                sys.exit()
            print("Private Key from DER: \n" + privKey.getXml())
            rsaDecryptor.put_EncodingMode(ENCODE_MODE)
            # import private key
            success = rsaDecryptor.ImportPrivateKey(privKey.getXml())
            if not success:
                print(rsaDecryptor.lastErrorText())
                sys.exit()
            return rsaDecryptor

    def initTCPServ(self): 
        """ Init the tcp server.
        """
        # Create the TCP server 
        try:
            tcpSer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSer.bind((TCP_IP, TCP_PORT))
            tcpSer.listen(1)
            return tcpSer
        except:
            print("TCP socket init error")
            raise

    def checkLogin(self, userName, password):
        return userName == '123' and password == '123'


    def startServer(self):

        terminate = False

        while not terminate:
            # Add the reconnection handling
            try:
                conn, addr = self.tcpServer.accept()
                print('Connection address:'+str(addr))
                while not terminate:
                    data = conn.recv(BUFFER_SIZE)
                    if not data: break # get the ending message. 
                    print("received data:"+str(data))
                    # Handle the client request.
                    if data == b'login':
                        conn.send(b'Done')
                    elif data == b'Fetch':
                        f_send = "publickey.cer"
                        with open(f_send, "rb") as f:
                            data = f.read()
                            conn.sendall(data)
                    else:
                        dataStr= data.decode('utf-8')
                        if dataStr[:2] == 'L;':
                            args =  dataStr.split(';')
                            tag = args[0]
                            if tag == 'L':
                                if self.checkLogin(args[1], args[2]):
                                    # send the cer file for sign the file: 
                                    conn.send(b'Done')
                                else:
                                    conn.send(b'Fail')
                        else:
                            encryptedStr = dataStr
                            print("decode the input string")
                            usePrivateKey = True
                            decryptedStr = self.rsaDecryptor.decryptStringENC(encryptedStr,usePrivateKey)
                            data = json.loads(decryptedStr)
                            print("Decripted message: \n" + str(data))

            except:
                continue


def startServ():
    server = FirmwServ()
    print("Server inited.")
    server.startServer()

if __name__ == '__main__':
    startServ()
