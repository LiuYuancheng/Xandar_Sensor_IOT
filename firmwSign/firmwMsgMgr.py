#-----------------------------------------------------------------------------
# Name:        firmwMsgMgr.py
#
# Purpose:     This module is used create a message manager to dump the user 
#              message to a json and Bytes data. 
# Author:      Yuancheng Liu
#
# Created:     2019/05/09
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------
import os
import json
import time

CMD_TYPE = 'C'.encode('utf-8')  # cmd type message used for contorl.  
FILE_TYPE = 'F'.encode('utf-8') # file(bytes) type.
RAN_LEN = 4

# Action type:
# CR    - Connection request
# HB    - Heart beat (feedback)
# LI1   - Login step1
# LR1   - Login response 1
# LI2   - login step2
# LR2   - login response 2
# LI3   - login step3
# LR3   - login response 3
# CF    - certificate Fetch.    
# SR    - signature response

class msgMgr(object):
    
    def __init__(self, parent):
        self.parent = parent
        self.data = None

    def dumpMsg(self, action=None, dataArgs=None):
        datab = None
        if action == 'CR':
            datab = self.createCRmsg()
        elif action == 'HB':
            lastAct, state = dataArgs
            datab = self.createHBmsg(lastAct, state)
        elif 'LI' in action:
            #print(action)
            datab = self.createLImsg(args=dataArgs)
        elif 'LR' in action:
            datab = self.createLRmsg(dataArgs)
        elif action == 'CF':
            datab = self.createCFmsg()
        elif action == 'FL':
            datab = self.createFLmsg(dataArgs)
        elif action == 'SR':
            datab = self.createSRmsg(dataArgs)
        #print(datab)
        return datab

    def createCRmsg(self):
        msgDict = {
            "act":  'CR',
            "time": time.time()
        }
        tag = CMD_TYPE
        data = json.dumps(msgDict).encode('utf-8')
        return tag + data

    def createHBmsg(self, lastAct, state):
        msgDict = {
            "act":  'HB',
            "lAct": lastAct, # last received action 
            "state": state      # last state. 
        }
        tag = CMD_TYPE
        data = json.dumps(msgDict).encode('utf-8')
        return tag + data

    def createLImsg(self, args = None):
        #print(args)
        if args is None:
            return None 
        if len(args) == 1:
            userName = args[0]
            randomB = os.urandom(RAN_LEN)
            msgDict = {
                "act"       : 'LI1',
                "user"      : str(userName),
                "random1"   : randomB.hex() 
            }
            data = CMD_TYPE + json.dumps(msgDict).encode('utf-8')
            return (data, randomB)
        elif len(args) == 2:
            (randomB, password) = args
            msgDict = {
                "act"       : 'LI2',
                "random2"   : randomB,
                "password"   : password 
            }
            data = CMD_TYPE + json.dumps(msgDict).encode('utf-8')
            return data

    def createLRmsg(self, args = None):
        if len(args) == 1:
            challenge = args[0]
            msgDict = {
                "act"       : 'LR2',
                "challenge" : challenge,
            }
            data = CMD_TYPE + json.dumps(msgDict).encode('utf-8')
            return data
        elif len(args) == 2:
            (randomB, state) = args
            randomB2 = os.urandom(RAN_LEN)
            msgDict = {
                "act"       : 'LR1',
                "state"     : state,
                "random1"   : randomB,
                "random2"   : randomB2.hex() 
            }
            data = CMD_TYPE + json.dumps(msgDict).encode('utf-8')
            return (data, randomB2)

    def createCFmsg(self):
        msgDict = {
            "act":  'CF',
            "time": time.time()
        }
        tag = CMD_TYPE
        data = json.dumps(msgDict).encode('utf-8')
        return tag + data

    def createSRmsg(self, args):
        sensorId, signerId,swatt , date, typeS, versionS, signS = args
        msgDict = {
            "act"   : 'SR',
            "id"    : sensorId,
            "sid"   : signerId,
            "swatt" : swatt,
            "date"  : date,
            "tpye"  : typeS,
            "version": versionS,
            "signStr": signS.hex()
        }
        tag = CMD_TYPE
        data = json.dumps(msgDict).encode('utf-8')
        return tag + data

    def createFLmsg(self, bytesData):
        tag = FILE_TYPE
        return tag + bytesData

    def loadMsg(self, msg):
        tag = msg[0:1]
        if tag == CMD_TYPE:
            data = msg[1:]
            return json.loads(data)
        elif tag == FILE_TYPE:
            data = msg[1:]
            return data

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase():
    testMsgr = msgMgr(None)
    print("Start the message process test:")
    print("Connection request test:")
    msgkey = ("act", "time")
    msg = testMsgr.createCRmsg()
    msgDict = testMsgr.loadMsg(msg)
    tPass = 0
    for i in msgkey:
        if i in msgDict.keys():
            tPass += 1
    if tPass == len(msgkey):
        print("Connection request test pass \n =")

    print("Heart beat test:")
    msgkey = ("act", "time")
    msg = testMsgr.createHBmsg()
    msgDict = testMsgr.loadMsg(msg)
    tPass = 0
    for i in msgkey:
        if i in msgDict.keys():
            tPass += 1
    if tPass == len(msgkey):
        print("Connection request test pass")


if __name__ == '__main__':
    testCase()