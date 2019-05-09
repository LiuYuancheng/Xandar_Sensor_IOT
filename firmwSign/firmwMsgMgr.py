import os
import json
import time

CMD_TYPE = 'C'.encode('utf-8')
FILE_TYPE = 'F'.encode('utf-8')
RAN_LEN = 4

# Action type:
# CR    - Connection request
# HB     - Heart beat
# LI1   - Login step1
# LR1   - Login response 1
# LI2   - login step2
# LR2   - login response 2
# LI3   - login step3
# LR3   - login response 3
# CF    - certificate Fetch.    

class msgTrans(object):
    
    def __init__(self):
        self.data = None

    def dumpMsg(self, action, dataArgs=None):
        if action == 'CR':
            self.createCRmsg()
            pass
        
        pass

    def createCRmsg(self):
        msgDict = {
            "act":  'CR',
            "time": time.time()
        }
        tag = CMD_TYPE
        data = json.dumps(msgDict).encode('utf-8')
        return tag + data

    def createHBmsg(self):
        msgDict = {
            "act":  'HB',
            "time": time.time()
        }
        tag = CMD_TYPE
        data = json.dumps(msgDict).encode('utf-8')
        return tag + data

    def createLImsg(self, args = None):
        if len(args) == 1:
            (userName) = args
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
                "random1"   : password 
            }
            data = CMD_TYPE + json.dumps(msgDict).encode('utf-8')
            return data

    def createLRmsg(self, args = None):
        if len(args) == 1:
            (liStatus) = args
            msgDict = {
                "act"       : 'LR2',
                "state"      : liStatus,
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

    def loadMsg(self, msg):
        tag = msg[0:1]
        if tag == CMD_TYPE:
            data = msg[1:]
            return json.loads(data)

def testCase():
    testMsgr = msgTrans()
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