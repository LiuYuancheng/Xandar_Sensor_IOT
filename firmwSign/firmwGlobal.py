#-----------------------------------------------------------------------------
# Name:        firmwGlobal.py
#
# Purpose:     This module is used set the Local config file as global value 
#              which will be used in the other modules.
# Author:      Yuancheng Liu
#
# Created:     2019/05/17
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------
import os


dirpath = os.getcwd()
print("Current working directory is : %s" %dirpath)

# Server ip and port for connection: 
SERVER_CHOICE = {
    "LocalDefault [127.0.0.1]"  : ('127.0.0.1', 5006),
    "Server_1 [192.168.0.100]"  : ('192.168.0.100', 5006),
    "Server_2 [192.168.0.101]"  : ('192.168.0.101', 5006)
}

# Data received buffer size:
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response

# Data message dump and load tag
CMD_TYPE = 'C'.encode('utf-8')  # cmd type message used for contorl.
FILE_TYPE = 'F'.encode('utf-8') # file(bytes) type.

RAN_LEN = 4 # The random number/bytes length.

# sqlite database file.
DB_PATH = "".join([dirpath, "\\firmwSign\\firmwDB.db"])



CA_PATH = "".join([dirpath, "\\firmwSign\\testCert\\CA.cert"])
CSSL_PRIK_PATH = "".join([dirpath, "\\firmwSign\\testCert\\client.pkey"])
CSSL_CERT_PATH = "".join([dirpath, "\\firmwSign\\testCert\\client.cert"])