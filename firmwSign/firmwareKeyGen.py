#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        firmwareKeyGen.py
#
# Purpose:     Use Openssl lib to generate the X509 private&public key and 
#              certificate under <*.pem> format, then verify a string.  
# Author:      Yuancheng Liu
#
# Created:     2019/05/08
# Copyright:   YC
# License:     YC
#------------------------------------------------------------------------
from OpenSSL import crypto

_k = crypto.PKey()
_cert = crypto.X509()

# Create RSA2048 keys
_k.generate_key(crypto.TYPE_RSA, 2048)

# Add argument for create certificate
_cert.gmtime_adj_notBefore(0)
_cert.gmtime_adj_notAfter(0*365*24*60*60)  # 10 years expiry date
_cert.set_pubkey(_k)
_cert.sign(_k, 'sha256')

#-------------------------------------------------------------------------------
# Create key's file
with open("public_key.pem", 'wb') as f:
    f.write(crypto.dump_publickey(crypto.FILETYPE_PEM, _k))

with open("private_key.pem", 'wb') as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, _k))

with open("certificate.pem", 'wb') as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, _cert))

#-------------------------------------------------------------------------------
# Open key and load in var
with open("private_key.pem", 'rb') as f:
    priv_key = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())

#with open("firmwSign\\testCert\\client.pkey",'rb') as f:
#    priv_key = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())

with open("public_key.pem", 'rb') as f:
    pub_key = crypto.load_publickey(crypto.FILETYPE_PEM, f.read())

with open("certificate.pem", 'rb') as f:
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())

#with open("firmwSign\\testCert\\client.cert",'rb') as f:
#    cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())

#-------------------------------------------------------------------------------
# sign message 'hello world' with private key and certificate
sign = crypto.sign(priv_key, b'hello world', 'sha256')

result = crypto.verify(cert, sign, b'hello world', 'sha256')

if result is None:
    print("The significure is verified.")
