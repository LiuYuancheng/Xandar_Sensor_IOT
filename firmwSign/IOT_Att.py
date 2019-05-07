#!/usr/bin/python
# -----------------------------------------------------------------------------
# Name:        IOT_ATT.py
#
# Purpose:     This module is used to provide a SWATT calculator to get the
# 			   input file's swatt value.
# Author:      Mohamed Haroon Basheer
#
# Created:     2019/05/06
# Copyright:
# License:
# -----------------------------------------------------------------------------
import os
import random
import string
import mimetypes
from uuid import getnode as get_mac

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class swattCal(object):
    """ This module is used to provide a SWATT calculator to get the input file's 
        swatt value.
    """
    # -----------------------------------------------------------------------------
    def __init__(self):
        self.p = 0
        self.q = 0
        self.state = None

    # -----------------------------------------------------------------------------
    def bitExtracted(self, number, k, s):
        """ Extract specified length of bits """
        return (((1 << k) - 1)  &  (number >> (s-1) ) )

    # -----------------------------------------------------------------------------
    def extract_CRpair(self, challenegeStr):
        """ Extract challenege response pair for the given key and iteration """
        final = self.bitExtracted(get_mac(),16,1) #UNIQUE PUFF VALUE FOR EACH DEVICE
        test = [(ord(k)^final) for k in challenegeStr]	
        for idx in range(len(challenegeStr)):
            if(idx !=len(test)-1):
                test[idx] = test[idx]^test[idx+1]
                final += test[idx]<<2
            else:
                final += test[idx]<<2
            idx += 1
        return final

    # -----------------------------------------------------------------------------
    def setKey(self, key,m):
        """RC4 Key Scheduling Algorithm (KSA)"""
        self.state = [n for n in range(m)] #fill with numnber ranging from 0 to 255
        self.p = self.q = j = 0
        for i in range(m):
            j = (j + self.state[i] + key[i % len(key)]) % m
            self.state[i], self.state[j] = self.state[j], self.state[i]

    # -----------------------------------------------------------------------------
    def string_to_list(self, inputString):
        """Convert a string into a byte list"""
        return [ord(c) for c in inputString] #returns the corresponding unicode integer for the char for ex; a==97

    # -----------------------------------------------------------------------------
    def getSWATT(self, challengeStr, m, filePath):
        """ Calculate the file swatt value based on the input challenge string
            and the iterative count. 
        """
        if not os.path.exists(filePath):
            print("The file <%s> is not exist" % filePath)
            return None
        fh = open(filePath, "rb")
        self.setKey(self.string_to_list(challengeStr), m)
        cr_response = self.extract_CRpair(challengeStr)  # P(C)
        init_cs = cr_response ^ m  # sigma(0)<--p(c) xor x0
        pprev_cs = self.state[256]  # c[(j-2)mod 8]
        prev_cs = self.state[257]  # c[(j-1)mod 8]
        current_cs = self.state[258]  # c[j]
        init_seed = m  # set x(i-1)
        # print init_cs.bit_length(),bin(init_cs),init_cs
        for i in range(m):
            swatt_seed = cr_response ^ init_seed  # y(i-1)=p(c) xor x(i-1)
            Address = (self.state[i] << 8)+prev_cs  # (RC4i<<8)+c[(j-1)mod 8]
            #use python PRG to generate address Range
            random.seed(Address)
            Address = random.randint(1, 128000)
            # read the EEPROM Memory content
            fh.seek(Address)
            strTemp = fh.read(1)
            #calculate checksum at the location
            if not strTemp: continue # jump over the empty str ""
            # current_cs=current_cs+(ord(strTemp[0])^pprev_cs+state[i-1])
            current_cs = current_cs+(ord(strTemp) ^ pprev_cs+self.state[i-1])
            # extra seed for the SWATT
            init_seed = current_cs+swatt_seed
            # update current_cs
            current_cs = current_cs >> 1
            # update c[(j-2)mod 8] & c[(j-1)mod 8]
            pprev_cs = prev_cs
            prev_cs = current_cs
        return hex(hash(current_cs))

# -----------------------------------------------------------------------------
# Lib function test case(we will do this in the future.)
#def testCase():
#    server = swattCal()
#    print("Start test.")
#    result = server.getSWATT("Testing", 300. None)
#    if reuslt == b'0x3c56': print("Test pass")

#if __name__ == '__main__':
#    testCase()


