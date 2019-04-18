#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Name:        TCP.py
#
# Purpose:     A TCP client program used to connect to the sensor reader program
#              to pull down the data.
# Author:      Yuancheng Liu
#
# Created:     2019/03/27
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------

import socket
import time
from sense_hat import SenseHat

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = "request data."
pIactiveFlag = True

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
# Init the sensHat contorl
sense = SenseHat()
sense.show_message('Ready')

for i in range(10):
    s.send(MESSAGE)
    data = s.recv(BUFFER_SIZE)
    time.sleep(1)
    print ("received data:"+str(data))
    Id, crt, avg = str(data).split('-')
    sense.show_message('>'+str(avg), text_colour=(0,255,0))

s.close()
