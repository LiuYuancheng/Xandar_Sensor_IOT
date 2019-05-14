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
# LO    - Logout requst.
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
            datab = self._createLImsg(args=dataArgs)
        elif 'LR' in action:
            datab = self._createLRmsg(dataArgs)
        elif action == 'CF':
            datab = self._createCFmsg()
        elif action == 'FL':
            datab = self._createFLmsg(dataArgs)
        elif action == 'SR':
            datab = self._createSRmsg(dataArgs)
        elif action == 'LO':
            datab = self._createLOmsg()
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
    def _createLOmsg(self):
        """Create a log out requst."""
        msgDict = {
            "act"   : 'LO',
            "time"  : time.time()
        }
        return CMD_TYPE + json.dumps(msgDict).encode('utf-8')

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
    pCount = 0 
    #
    tPass = True
    print("Connection request test:")
    msg = testMsgr.dumpMsg(action='CR')
    msgDict = testMsgr.loadMsg(msg)
    tPass = tPass and msgDict['act'] == 'CR'
    tPass = tPass and 'time' in msgDict.keys()
    if tPass:
        pCount += 1
        print("Connection request test pass")
    else:
        print("Connection request test fail")
    #
    tPass = True
    print("HearBeat message test:")
    msg = testMsgr.dumpMsg(action='HB', dataArgs=('HB', 1))
    msgDict = testMsgr.loadMsg(msg)
    tPass = tPass and msgDict['act'] == 'HB'
    tPass = tPass and msgDict['lAct'] == 'HB'
    tPass = tPass and msgDict['state'] == 1
    if tPass:
        pCount += 1
        print("HeartBeat request test pass")
    else:
        print("HeartBeat request test fail")
    #
    tPass = True
    print("Login user request test:")
    msg, val = testMsgr.dumpMsg(action='LI', dataArgs='user')
    msgDict = testMsgr.loadMsg(msg)    
    tPass = tPass and msgDict['act'] == 'LI1'
    tPass = tPass and msgDict['user'] == 'user'
    tPass = tPass and val.hex() == msgDict['random1']
    if tPass:
        pCount += 1
        print("Login user request test pass")
    else:
        print("Login user request test fail")
    # 
    tPass = True
    print("Login password request test:")
    msg = testMsgr.dumpMsg(action='LI2', dataArgs=('1234', 'password'))
    msgDict = testMsgr.loadMsg(msg)
    tPass = tPass and msgDict['act'] == 'LI2'
    tPass = tPass and msgDict['random2'] == '1234'
    tPass = tPass and msgDict['password'] == 'password'
    if tPass:
        pCount += 1
        print("Login password request test pass")
    else:
        print("Login password request test fail")
    # 
    tPass = True
    print("Login user response test:")
    msg, val = testMsgr.dumpMsg(action='LR', dataArgs=('1234', 1))
    msgDict = testMsgr.loadMsg(msg)
    tPass = tPass and msgDict['act'] == 'LR1'
    tPass = tPass and msgDict['state'] == 1
    tPass = tPass and msgDict['random1'] == '1234'
    tPass = tPass and msgDict['random2'] == val.hex()
    if tPass:
        pCount += 1
        print("Login user response test pass")
    else:
        print("Login suer response test fail")
    #
    tPass = True
    print("Login password response test:")
    msg = testMsgr.dumpMsg(action='LR', dataArgs='challenge')
    msgDict = testMsgr.loadMsg(msg)
    tPass = tPass and msgDict['act'] == 'LR2'
    tPass = tPass and msgDict['challenge'] == 'challenge'
    if tPass:
        pCount += 1
        print("Login password response test pass")
    else:
        print("Login password response test fail")
    #
    tPass = True
    print("Certificate fetch request test:")
    msg = testMsgr.dumpMsg(action='CF')
    msgDict = testMsgr.loadMsg(msg)
    tPass = tPass and msgDict['act'] == 'CF'
    tPass = tPass and msgDict['time']
    if tPass:
        pCount += 1
        print("Certificate fetch test pass")
    else:
        print("Certificate fetch test fail")
    #
    tPass = True
    print("Logout request test:")
    msg = testMsgr.dumpMsg(action='LO')
    msgDict = testMsgr.loadMsg(msg)
    tPass = tPass and msgDict['act'] == 'LO'
    tPass = tPass and msgDict['time']
    if tPass:
        pCount += 1
        print("Logout requset test pass")
    else:
        print("Logout requset test fail")

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    testCase()
