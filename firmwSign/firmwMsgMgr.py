#-----------------------------------------------------------------------------
# Name:        firmwMsgMgr.py
#
# Purpose:     This module is used create a message manager to dump the user 
#              message to a json string/bytes data and load back to orignal
#              data.(the detail usage you can follow the example in testCase) 
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
RAN_LEN = 4 # The random number/bytes length.
# Action type:
# CR    - Connection request
# HB    - Heart beat (feedback)
# LI1   - Login request step 1 [Username + random1(client->sever)]
# LR1   - Login response 1 [random1 + random2(client<-server)]
# LI2   - Login request step2 [random2 + password]
# LR2   - Login response 2 [Challenge for SWATT]
# CF    - Certificate file fetch.    
# SR    - Signature response

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class msgMgr(object):
    """ Create a message manager to dump the user message to a json string/bytes
        data and load back to orignal data.
    """
    def __init__(self, parent):
        self.parent = parent
        self.data = None

#-----------------------------------------------------------------------------
    def dumpMsg(self, action=None, dataArgs=None):
        """ Create the bytes message base on the action for sending to server.
        """
        datab = None
        if action == 'CR':
            datab = self._createCRmsg()
        elif action == 'HB':
            lastAct, state = dataArgs
            datab = self._createHBmsg(lastAct, state)
        elif 'LI' in action:
            #print(action)
            datab = self._createLImsg(args=dataArgs)
        elif 'LR' in action:
            datab = self._createLRmsg(dataArgs)
        elif action == 'CF':
            datab = self._createCFmsg()
        elif action == 'FL':
            datab = self._createFLmsg(dataArgs)
        elif action == 'SR':
            datab = self._createSRmsg(dataArgs)
        return datab

#-----------------------------------------------------------------------------
    def loadMsg(self, msg):
        """ Convert the dumpped message back to orignal data.
        """
        tag = msg[0:1] # Take out the tag data.
        data = json.loads(msg[1:]) if tag == CMD_TYPE else msg[1:]
        return data

#-----------------------------------------------------------------------------
    def _createCRmsg(self):
        """ Create the connection request message.
        """
        msgDict = {
            "act"   : 'CR',
            "time"  : time.time()
        }
        return CMD_TYPE + json.dumps(msgDict).encode('utf-8')

#-----------------------------------------------------------------------------
    def _createHBmsg(self, lastAct, state):
        """ Create a heart beat function to handle the cmd execution response.
        """
        msgDict = {
            "act"   : 'HB',
            "lAct"  : lastAct,  # last received action 
            "state" : state     # last action exe state.(0/1)
        }
        return CMD_TYPE + json.dumps(msgDict).encode('utf-8')

#-----------------------------------------------------------------------------
    def _createLImsg(self, args=None):
        """ Create a login message: 
            login step1: send userName + randomNum1
            login step2: send randomNum2 + password
        """ 
        if args is None: return None 
        if isinstance(args, str):
            userName = args.strip()  # remove the user space.
            randomB = os.urandom(RAN_LEN)
            msgDict = {
                "act"   : 'LI1',
                "user"  : str(userName),
                "random1": randomB.hex()
            }
            data = CMD_TYPE + json.dumps(msgDict).encode('utf-8')
            return (data, randomB)
        elif len(args) == 2:
            (randomB, password) = args
            msgDict = {
                "act"       : 'LI2',
                "random2"   : randomB,
                "password"  : password 
            }
            data = CMD_TYPE + json.dumps(msgDict).encode('utf-8')
            return data

#-----------------------------------------------------------------------------
    def _createLRmsg(self, args=None):
        """ Create a login request.
        """ 
        if args is None: return args
        if isinstance(args, str):
            challenge = args.strip()
            msgDict = {
                "act"       : 'LR2',
                "challenge" : challenge,
            }
            return CMD_TYPE + json.dumps(msgDict).encode('utf-8')
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

#-----------------------------------------------------------------------------
    def _createCFmsg(self):
        """ Create a certificate file fetch requset.
        """
        msgDict = {
            "act"   : 'CF',
            "time"  : time.time()
        }
        return CMD_TYPE + json.dumps(msgDict).encode('utf-8')

#-----------------------------------------------------------------------------
    def _createSRmsg(self, args):
        """ Create a sign response message. 
        """
        if len(args) != 7:
            print("The required message in the message list missing<%s>" %str(args))
            return None
        sensorId, signerId, swatt, date, typeS, versionS, signS = args
        msgDict = {
            "act"   : 'SR',     
            "id"    : sensorId,     # sensor ID
            "sid"   : signerId,     # Signer factory user ID.
            "swatt" : swatt,        # File SWATT value. 
            "date"  : date,         # time stamp.
            "tpye"  : typeS,        # Sensor type.
            "version": versionS,    # Sensor version.
            "signStr": signS.hex()  # Signature string.
        }
        return CMD_TYPE + json.dumps(msgDict).encode('utf-8')

#-----------------------------------------------------------------------------
    def _createFLmsg(self, bytesData):
        """ Create the file message.
        """
        return FILE_TYPE + bytesData

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# TODO: finished the test case.
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
    msg = testMsgr.createHBmsg( None, 0)
    msgDict = testMsgr.loadMsg(msg)
    tPass = 0
    for i in msgkey:
        if i in msgDict.keys():
            tPass += 1
    if tPass == len(msgkey):
        print("Connection request test pass")

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    testCase()
