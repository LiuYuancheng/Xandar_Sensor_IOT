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
import random
import string
import socket
import chilkat
import IOT_Att as SWATT

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response


dirpath = os.getcwd()
print("current directory is : " + dirpath)

CERT_PATH = "".join([dirpath, "\\publickey.cer"])
PRI_PATH = "".join( [dirpath, "\\privatekey.pem"])
DEFUALT_FW= "".join([dirpath, "\\firmwareSample"])


ENCODE_MODE = 'base64' # or 'hex'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class FirmwServ(object):
    
    def __init__(self):

        self.rsaDecryptor = self.initDecoder(Mode='RSA')
        self.tcpServer = self.initTCPServ()
        self.swattHd =  SWATT.swattCal()
        self.responseEpc = None # expect response of the firmware file.

    def initDecoder(self, Mode=None):
        """ init the message decoder. 
        """
        if not Mode:
            print("Decode mode missing.")
            return None
        elif Mode == 'RSA':
            rsaDecryptor = chilkat.CkRsa()
            if not rsaDecryptor.UnlockComponent("Anything for 30-day trial"):
                print("RSA component unlock failed")
                return None
            privKey = chilkat.CkPrivateKey()
            success = privKey.LoadPemFile(PRI_PATH)
            if not success:
                print(privKey.lastErrorText())
                return None
            print("Private Key from DER: \n" + privKey.getXml())
            rsaDecryptor.put_EncodingMode(ENCODE_MODE)
            # import private key
            success = rsaDecryptor.ImportPrivateKey(privKey.getXml())
            if not success:
                print(rsaDecryptor.lastErrorText())
                return None
            return rsaDecryptor

#-----------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------
    def randomChallStr(self, stringLength=10):
        """Generate a random chanllenge string of fixed length """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

#-----------------------------------------------------------------------------
    def checkLogin(self, userName, password):
        return userName == '123' and password == '123'

#-----------------------------------------------------------------------------
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
                    # Handle the login request.
                    if data == b'login':
                        conn.send(b'Done')
                    # Handle the certificate fetch request.
                    elif data == b'Fetch':
                        f_send = "publickey.cer"
                        with open(f_send, "rb") as f:
                            data = f.read()
                            conn.sendall(data)
                    else:
                        dataStr= data.decode('utf-8')
                        # Handle the username and password.
                        if dataStr[:2] == 'L;':
                            args =  dataStr.split(';')
                            tag = args[0]
                            if tag == 'L':
                                if self.checkLogin(args[1], args[2]):
                                    # send the cer file for sign the file:
                                    chaStr = self.randomChallStr(stringLength=10)
                                    print("This is the challenge: %s" %chaStr)
                                    self.responseEpc = self.swattHd.getSWATT(chaStr, 300, DEFUALT_FW)
                                    print("This is the swatt: %s" %str(self.responseEpc))
                                    conn.send(str(chaStr).encode('utf-8'))
                                else:
                                    conn.send(b'Fail')
                        # Handle the signed message.
                        else:
                            encryptedStr = dataStr
                            print("decode the input string")
                            usePrivateKey = True
                            decryptedStr = self.rsaDecryptor.decryptStringENC(encryptedStr,usePrivateKey)
                            data = json.loads(decryptedStr)
                            print("Decripted message: \n" + str(data))
                            if data['swatt'] == self.responseEpc:
                                print("The firmware is signed successfully")

            except:
                continue

#-----------------------------------------------------------------------------
def startServ():
    server = FirmwServ()
    print("Server inited.")
    server.startServer()

if __name__ == '__main__':
    startServ()
