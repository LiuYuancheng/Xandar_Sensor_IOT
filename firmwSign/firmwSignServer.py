#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        firmwareSignServer.py
#
# Purpose:     This module is used to connect to the firmware sign client and:
#               - Check wehther the certificate fetch request is valid.
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
import threading
import IOT_Att as SWATT
import firmwDBMgr as DataBase
import firmwMsgMgr
import firmwTLSserver as SSLS
import firmwTAServer as TAS
import firmwGlobal as gv
from OpenSSL import crypto

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class FirmwServ(object):
    """ Main firmware sign authorization server program.
    """
    def __init__(self):
        """ Init the parameters."""
        self.cert = None
        self.loginUser = None
        self.ownRandom = None
        self.priv_key = None
        self.responseEpc = None # expect response of the firmware file.
        self.ranStr = "" # random string used for Swatt challenge set.
        #self.rsaDecryptor = self.initDecoder(Mode='RSA')
        self.sslServer = SSLS.TLS_sslServer(self) # changed to ssl client
        self.sslServer.serverSet(port = gv.SITCP_PORT, listen=1, block=1 )
        # Init the communication server.
        self.tcpServer = self.initTCPServ() if self.sslServer is None else self.sslServer
        # Init the sign cert verifier.
        self.initVerifier() 
        # Init the SWA-TT calculator. 
        self.swattHd =  SWATT.swattCal()
        # Init the communication message manager. 
        self.msgMgr= firmwMsgMgr.msgMgr(self) # create the message manager.
        # Init the database manager. 
        self.dbMgr = DataBase.firmwDBMgr()
        # Init the sensor register thread
        self.rgThread = rgCommThread(1, "RG_response_thread", self.dbMgr)
        self.rgThread.start()
        # Init the trustClient Server
        #self.taThread = taCommThread(2, "TA_server_thread")
        #self.rgThread.start()


#-----------------------------------------------------------------------------
    def checkLogin(self, userName, password):
        """ Connect to db to authorize user+password """
        return self.dbMgr.authorizeUser(userName, password)

#-----------------------------------------------------------------------------
    def handleAuthrozie(self, sender, dataDict):
        """ Authrozie the user password."""
        if bytes.fromhex(dataDict['random2']) == self.ownRandom:
            if self.dbMgr.authorizeUser(self.loginUser, dataDict['password']):
                print("Login2: User login password correct.")
                self.ranStr = self.randomChallStr(stringLength=10)
                reply = self.msgMgr.dumpMsg(action='LR2',dataArgs=self.ranStr)
                sender.send(reply)
                return True # return if the user password is correct.
            else:
                print("Login2: User password incorrect.")
        # feed back user login fail if the password is incorrect.
        reply = self.msgMgr.dumpMsg(action='HB',dataArgs=('LI2', 0))
        sender.send(reply)

#-----------------------------------------------------------------------------
    def handleCertFetch(self, sender, dataDict):
        """handle the certificate fetch request."""
        f_send = gv.SIGN_PRIV_PATH
        # f_send = "publickey.cer" # use the RSA file.
        with open(f_send, "rb") as f:
            reply = self.msgMgr.dumpMsg(action='FL', dataArgs=f.read())
            sender.send(reply)

#-----------------------------------------------------------------------------
    def handleConnection(self, sender, dataDict):
        """ handle the client connection request."""
        reply = self.msgMgr.dumpMsg(action='HB', dataArgs=('CR', 1))
        sender.send(reply)

#-----------------------------------------------------------------------------
    def handleLogin(self, sender, dataDict):
        """ Handle the user login request."""
        self.loginUser = dataDict['user']
        if self.dbMgr.checkUser(self.loginUser):
            print("Login1: find the user")
            reply, self.ownRandom = self.msgMgr.dumpMsg(action='LR1',dataArgs=(dataDict['random1'], 1))
            sender.send(reply)
        else:
            print("Login1: the user<%s> is not in data base." %str(self.loginUser))
            self.loginUser = None
            reply = self.msgMgr.dumpMsg(action='HB',dataArgs=('LI1', 0))
            sender.send(reply)

#-----------------------------------------------------------------------------
    def handleLogout(self):
        """ handle user logout: clear all the parameters"""
        self.loginUser = None
        self.ownRandom = None
        self.responseEpc = None
        self.ranStr = ""

#-----------------------------------------------------------------------------
    def handleSignResp(self, sender, dataDict):
        """ Parse the sign feed back message and verify the sign correction."""
        checkStr = ''.join([str(dataDict['id']),
                            str(dataDict['sid']),
                            str(dataDict['swatt']),
                            str(dataDict['date']),
                            str(dataDict['tpye']),
                            str(dataDict['version'])
                            ])
        # Below comments part is user the old RSA sign verify method.
        #encryptedStr = dataDict['signStr']
        #print("decode the signature string")
        #usePrivateKey = True
        #decryptedStr = self.rsaDecryptor.decryptStringENC(encryptedStr,usePrivateKey)
        sign = bytes.fromhex(dataDict['signStr'])
        try:
            # <crypto.verify> return None if verify, else return exception.
            if crypto.verify(self.cert, sign, checkStr.encode('utf-8'), 'sha256') is None:
                print("SignVerify: The result is correct.")
        except:
            print("SingVerify: The sign can not metch the data.")
            sender.send(self.msgMgr.dumpMsg(action='SR', dataArgs=('LI1', 0)))
            return False
        print("SingVerify: This is the decryptioin sstr: %s" % checkStr)

        # Double confirm the SWATT
        self.swattHd.setPuff(int(dataDict['sid']))
        self.responseEpc = self.swattHd.getSWATT(self.ranStr, 300, gv.DEFUALT_FW)
        if dataDict['swatt'] == self.responseEpc:
            print("SingVerify: the firmware is signed successfully")
            rcdList = [int(dataDict['id']), int(dataDict['sid']), self.ranStr,
                       str(dataDict['swatt']), dataDict['date'], dataDict['tpye'],
                       dataDict['version'], gv.SIGN_CERT_PATH, dataDict['signStr']]
            self.loadPrivateK(gv.SIGN_PRIV_PATH)
            dataStr = ''.join([str(n) for n in rcdList]).encode('utf-8')
            signatureServer = crypto.sign(self.priv_key, dataStr, 'sha256')
            rcdList.append(signatureServer.hex())
            self.dbMgr.createFmSignRcd(rcdList)
            reply = self.msgMgr.dumpMsg(action='HB', dataArgs=('SR', signatureServer))
            sender.send(reply)
        else:
            reply = self.msgMgr.dumpMsg(action='HB', dataArgs=('SR', 0))
            sender.send(reply)


    #-----------------------------------------------------------------------------
    def loadPrivateK(self, keyPath):
        """ load pricate key from the sertificate file.
        """
        if not os.path.exists(keyPath):
            print("The private key file used to sign input is not exist")
        with open(keyPath, 'rb') as f:
            self.priv_key = crypto.load_privatekey(
                crypto.FILETYPE_PEM, f.read())

#-----------------------------------------------------------------------------
    def initDecoder(self, Mode=None):
        """ Init the message decoder."""
        if not Mode:
            print("Decoder: decode mode missing.")
            return None
        elif Mode == 'RSA':
            rsaDecryptor = chilkat.CkRsa()
            if not rsaDecryptor.UnlockComponent("Anything for 30-day trial"):
                print("Decoder: RSA component unlock failed")
                return None
            privKey = chilkat.CkPrivateKey()
            success = privKey.LoadPemFile(gv.RSA_PRI_PATH)
            if not success:
                print(privKey.lastErrorText())
                return None
            print("Decoder: private Key from DER: \n" + privKey.getXml())
            rsaDecryptor.put_EncodingMode(gv.RSA_ENCODE_MODE)
            # import private key
            success = rsaDecryptor.ImportPrivateKey(privKey.getXml())
            if not success:
                print(rsaDecryptor.lastErrorText())
                return None
            return rsaDecryptor

#-----------------------------------------------------------------------------
    def initTCPServ(self): 
        """ Init the tcp server if we don't use SSL communication."""
        try:
            # Create the TCP server 
            tcpSer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSer.bind((gv.LOCAL_IP, gv.SITCP_PORT))
            tcpSer.listen(1)
            return tcpSer
        except:
            print("TCP: TCP socket init error.")
            raise

#-----------------------------------------------------------------------------
    def initVerifier(self):
        """Init the cerfiticate verifier."""
        with open(gv.CSSL_CERT_PATH,'rb') as f:
            self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
        print("Sign: Locaded the sign certificate file.")

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
        return os.urandom(stringLength).hex()

#-----------------------------------------------------------------------------
    def startServer(self):
        """ main server loop to handle the user's requst. """
        terminate = False
        while not terminate:
            # Add the reconnection handling
            try:
                conn, addr = self.tcpServer.accept()
                print('Connection: connection address:<%s>' %str(addr))
                while not terminate:
                    data = conn.recv(gv.BUFFER_SIZE)
                    if not data: break # get the ending message. 
                    print("Connection: received data:<%s>" %str(data))
                    dataDict = self.msgMgr.loadMsg(data)
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
                    elif dataDict['act'] == 'LO':
                        self.handleLogout()
                        break
                    else:
                        continue
            except:
                print("MainLoop: main loop error.")
                continue

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class rgCommThread(threading.Thread):
    """ Thread to opena SSL channel for the sensor registration function.""" 
    def __init__(self, threadID, name, dbMgr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.dbMgr = dbMgr # get the db manager from the server. 
        self.sslServer = SSLS.TLS_sslServer(self) # init ssl client.
        self.sslServer.serverSet(port = gv.RGTCP_PORT, listen=1, block=1 )
        self.tcpServer = self.sslServer
        self.msgMgr= firmwMsgMgr.msgMgr(self) # create the message manager.
        print("Register:  Thread init.")

    #-----------------------------------------------------------------------------
    def run(self):
        """ main server loop to handle the user's requst. """
        terminate = False
        while not terminate:
            # Add the reconnection handling
            try:
                conn, addr = self.tcpServer.accept()
                print('RGConnection: connection address:<%s>' %str(addr))
                while not terminate:
                    data = conn.recv(gv.BUFFER_SIZE)
                    if not data: break # get the ending message. 
                    print("RGConnection: received data:<%s>" %str(data))
                    dataDict = self.msgMgr.loadMsg(data)
                    # print(dataDict)
                    if dataDict['act'] == 'CR':
                        self.handleConnection(conn, dataDict)
                    elif dataDict['act'] == 'RG':
                        self.handleRigster(conn, dataDict)
                    elif dataDict['act'] == 'LO':
                        self.handleLogout()
                        break
                    else:
                        continue
            except:
                print("RGConnection: main loop error.")
                continue

    #-----------------------------------------------------------------------------
    def handleRigster(self, sender, dataDict):
        """ handle the client connection request."""
        args = (dataDict['signStr'], dataDict['id'],
                dataDict['type'], dataDict['version'], dataDict['time'])
        result = self.dbMgr.authorizeSensor(args)
        reply = self.msgMgr.dumpMsg(action='HB', dataArgs=('RG', result))
        sender.send(reply)
    #-----------------------------------------------------------------------------
    def handleLogout(self):
        """ handle user logout: clear all the parameters"""
        print("RGConnection: sensor logout.")

    #-----------------------------------------------------------------------------
    def handleConnection(self, sender, dataDict):
        """ handle the client connection request."""
        reply = self.msgMgr.dumpMsg(action='HB', dataArgs=('CR', 1))
        sender.send(reply)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class taCommThread(threading.Thread):
    """ Thread to opena SSL channel for the sensor registration function.""" 
    def __init__(self, threadID, name, dbMgr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.taServer = TAS.firmwTAServer() # init TrustAPP server.
        print("TA server:  Thread init.")

    #-----------------------------------------------------------------------------
    def run(self):
        """ main server loop to handle the user's requst. """
        self.taServer.startServer()

#-----------------------------------------------------------------------------
def startServ():
    server = FirmwServ()
    print("Server inited.")
    server.startServer()

if __name__ == '__main__':
    startServ()
