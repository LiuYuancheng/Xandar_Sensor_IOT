import sys
import chilkat

rsa = chilkat.CkRsa()

success = rsa.UnlockComponent("Anything for 30-day trial")
if (success != True):
    print("RSA component unlock failed")
    sys.exit()

#  This example also generates the public and private
#  keys to be used in the RSA encryption.
#  Normally, you would generate a key pair once,
#  and distribute the public key to your partner.
#  Anything encrypted with the public key can be
#  decrypted with the private key.  The reverse is
#  also true: anything encrypted using the private
#  key can be decrypted using the public key.

#  Generate a 1024-bit key.  Chilkat RSA supports
#  key sizes ranging from 512 bits to 4096 bits.
success = rsa.GenerateKey(1024)
if (success != True):
    print(rsa.lastErrorText())
    sys.exit()

#  Keys are exported in XML format:
publicKey = rsa.exportPublicKey()
privateKey = rsa.exportPrivateKey()

plainText = "Encrypting and decrypting should be easy!"

#  Start with a new RSA object to demonstrate that all we
#  need are the keys previously exported:
rsaEncryptor = chilkat.CkRsa()

#  Encrypted output is always binary.  In this case, we want
#  to encode the encrypted bytes in a printable string.
#  Our choices are "hex", "base64", "url", "quoted-printable".
rsaEncryptor.put_EncodingMode("hex")
print(publicKey)
#  We'll encrypt with the public key and decrypt with the private
#  key.  It's also possible to do the reverse.
success = rsaEncryptor.ImportPublicKey(publicKey)

usePrivateKey = False
encryptedStr = rsaEncryptor.encryptStringENC(plainText,usePrivateKey)
print(encryptedStr)

#  Now decrypt:
rsaDecryptor = chilkat.CkRsa()

rsaDecryptor.put_EncodingMode("hex")
success = rsaDecryptor.ImportPrivateKey(privateKey)

usePrivateKey = True
decryptedStr = rsaDecryptor.decryptStringENC(encryptedStr,usePrivateKey)

print(decryptedStr)