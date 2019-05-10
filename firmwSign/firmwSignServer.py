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
import firmwDBMgr as DataBase
import firmwMsgMgr
from OpenSSL import crypto

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
RAN_LEN = 4

dirpath = os.getcwd()
print("current directory is : " + dirpath)

CERT_PATH = "".join([dirpath, "\\publickey.cer"])
PRI_PATH = "".join( [dirpath, "\\privatekey.pem"])
DEFUALT_FW= "".join([dirpath, "\\firmwareSample"])

# SHA-256 sign used
SCERT_PATH = "".join([dirpath, "\\certificate.pem"])
SPRIV_PATH = "".join([dirpath, "\\private_key.pem"])


ENCODE_MODE = 'base64' # or 'hex'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class FirmwServ(object):
    
    def __init__(self):
        
        self.rsaDecryptor = self.initDecoder(Mode='RSA')
        self.tcpServer = self.initTCPServ()
        self.cert = None
        self.initVerifier()
        self.swattHd =  SWATT.swattCal()
        self.msgMgr= firmwMsgMgr.msgMgr(self) # create the message manager.
        self.ranStr = ""
        self.loginUser = None
        self.ownRandom = None
        self.responseEpc = None # expect response of the firmware file.
        self.dbMgr = DataBase.firmwDBMgr()

    def initVerifier(self):
        with open(SCERT_PATH,'rb') as f:
            self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
        print("Sign: Locaded the sign certificate file.")

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
    def securRadeom(self, stringLength = 4):
        """  OpenSSL update 17.3.0 (2017-09-14)
            Removed the deprecated OpenSSL.rand module. This is being done 
            ahead of our normal deprecation schedule due to its lack of use 
            and the fact that it was becoming a maintenance burden. os.urandom()
            should be used instead
        """
        pass

#-----------------------------------------------------------------------------
    def checkLogin(self, userName, password):
        return self.dbMgr.authorizeUser(userName, password)


    def handleConnection(self, sender, dataDict):
        reply = self.msgMgr.dumpMsg(action='HB',dataArgs=('CR', 1))
        sender.send(reply)

    def handleLogin(self, sender, dataDict):
        self.loginUser = dataDict['user']
        if self.dbMgr.checkUser(self.loginUser):
            print("find the user")
            reply, self.ownRandom = self.msgMgr.dumpMsg(action='LR1',dataArgs=(dataDict['random1'], 1))
            sender.send(reply)
        else:
            self.loginUser = None
            reply = self.msgMgr.dumpMsg(action='HB',dataArgs=('LI1', 0))
            sender.send(reply)

    def handleAuthrozie(self, sender, dataDict):
        if bytes.fromhex(dataDict['random2']) == self.ownRandom:
            if self.dbMgr.authorizeUser(self.loginUser, dataDict['password']):
                print("user login")
                self.ranStr = self.randomChallStr(stringLength=10)
                reply = self.msgMgr.dumpMsg(action='LR2',dataArgs=(self.ranStr,))
                sender.send(reply)
        else:
            print("wrong user connected.")
            reply = self.msgMgr.dumpMsg(action='HB',dataArgs=('LI2', 0))
            sender.send(reply)

    def handleCertFetch(self, sender, dataDict):
        f_send = SPRIV_PATH
        # f_send = "publickey.cer" # user the file.
        with open(f_send, "rb") as f:
            data = f.read()
            reply = self.msgMgr.dumpMsg(action='FL', dataArgs=data)
            sender.send(reply)

    def handleSignResp(self, sender, dataDict):
        checkStr = ''.join([str(dataDict['id']), 
                            str(dataDict['sid']), 
                            str(dataDict['swatt']),
                            str(dataDict['date']),
                            str(dataDict['tpye']),
                            str(dataDict['version'])
                            ])
        encryptedStr = dataDict['signStr']
        print("decode the signature string")
        #usePrivateKey = True
        #decryptedStr = self.rsaDecryptor.decryptStringENC(encryptedStr,usePrivateKey)
        sign = bytes.fromhex(dataDict['signStr'])
        verifyR = crypto.verify(self.cert, sign, checkStr.encode('utf-8'), 'sha256')
        if verifyR is None: 
            print ("The result is correct.")        
        print("This is the decryptioin sstr:" + checkStr)
        # Double confirm the SWATT 
        self.responseEpc = self.swattHd.getSWATT(self.ranStr, 300, DEFUALT_FW)
        if dataDict['swatt'] == self.responseEpc:
            print("The firmware is signed successfully")
            rcdList = (int(dataDict['id']), int(dataDict['sid']), self.ranStr, str(dataDict['swatt']),
             dataDict['date'], dataDict['tpye'], dataDict['version'], SCERT_PATH, dataDict['signStr'])
            self.dbMgr.createFmSignRcd(rcdList)
            reply = self.msgMgr.dumpMsg(action='HB',dataArgs=('SR', 1))
            sender.send(reply)
        else:
            reply = self.msgMgr.dumpMsg(action='HB',dataArgs=('SR', 0))
            sender.send(reply)

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
                    dataDict = self.msgMgr.loadMsg(data)
                    print(dataDict)

                    if dataDict['act'] == 'CR':
                        self.handleConnection(conn, dataDict)
                    elif dataDict['act'] == 'LI1':
                        self.handleLogin(conn, dataDict)
                    elif dataDict['act'] == 'LI2':
                        self.handleAuthrozie(conn, dataDict)
                    elif dataDict['act'] == 'CF':
                        self.handleCertFetch(conn, dataDict)
                    elif dataDict['act'] == 'SR':
                        self.handleSignResp(conn, dataDict)

                    continue


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
                        dataTag= data[0:1].decode('utf-8')
                        # handle the log in
                        if dataTag == 'U':
                            # user login.
                            userName = data[1:-4]
                            userRanNum = data[-4:]
                            #
                            if self.dbMgr.checkUser(userName):
                                self.ownRandom = os.urandom(RAN_LEN)
                                conn.send(userRanNum+self.ownRandom)
                            else:
                                conn.send('uf'.encode('utf-8'))



                        # Handle the username and password.
                        if dataStr[:2] == 'L;':
                            args =  dataStr.split(';')
                            tag = args[0]
                            if tag == 'L':
                                if self.checkLogin(args[1], args[2]):
                                    # send the cer file for sign the file:
                                    self.ranStr = self.randomChallStr(stringLength=10)
                                    print("This is the challenge: %s" %self.ranStr)
                                    self.responseEpc = self.swattHd.getSWATT(self.ranStr, 300, DEFUALT_FW)
                                    print("This is the swatt: %s" %str(self.responseEpc))
                                    conn.send(str(self.ranStr).encode('utf-8'))
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
                                rcdList = (int(data['id']), self.ranStr, str(data['swatt']),data['date'], data['tpye'], data['version'])
                                self.dbMgr.createFmSignRcd(rcdList)

            except:
                continue

#-----------------------------------------------------------------------------
def startServ():
    server = FirmwServ()
    print("Server inited.")
    server.startServer()

if __name__ == '__main__':
    startServ()
