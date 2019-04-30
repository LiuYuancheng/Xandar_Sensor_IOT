import sys
import os
import ssl
from pprint import pprint as pp
import chilkat

def main():
    cert_file_name = os.path.join(os.path.dirname(__file__), "x509test.cer")
    try:
        cert_dict = ssl._ssl._test_decode_cert(cert_file_name)
        pp(cert_dict)
        print('------------')
        # get the public key
        cert = chilkat.CkCert()
        success = cert.LoadFromFile("C:\\Project\\testProgram\\IOT\\IOT\\firmwSign\\publickey.cer")
        if (success != True):
            print(cert.lastErrorText())
            sys.exit()
        #  DN = "Distinguished Name"
        
        print("SubjectDN:" + cert.subjectDN())

        print("Common Name:" + cert.subjectCN())
        print("Issuer Common Name:" + cert.issuerCN())

        print("Serial Number:" + cert.serialNumber())    
        pubKey = cert.ExportPublicKey()
        if (cert.get_LastMethodSuccess() != True):
            print(cert.lastErrorText())
            sys.exit()
        print(pubKey)
        print("key type = " + pubKey.keyType())
        #print(pubKey.getXml())

        xml = chilkat.CkXml()
        xml.LoadXml(pubKey.getXml())
        print("Public Key XML:")
        print(xml.getXml())

        modulus = xml.getChildContent("Modulus")
        print('----------')
        print("base64 modulus = " + modulus)

        #  To convert to hex:
        binDat = chilkat.CkBinData()
        binDat.Clear()
        binDat.AppendEncoded(modulus,"base64")
        hexModulus = binDat.getEncoded("hex")
        print("hex modulus = " + hexModulus)

        plainText = "Encrypting and decrypting should be easy!"
        rsaEncryptor = chilkat.CkRsa()

        # must do the unlocak process ? 
        success = rsaEncryptor.UnlockComponent("Anything for 30-day trial")
        if (success != True):
            print("RSA component unlock failed")
            sys.exit()

        rsaEncryptor.put_EncodingMode("hex")
        # encrype 
        print("encrypt the message")
        success = rsaEncryptor.ImportPublicKey(pubKey.getXml())
        print (success)
        
        usePrivateKey = False
        #success = rsaEncryptor.ImportPublicKey(pubKey)

        encryptedStr = rsaEncryptor.encryptStringENC(plainText,usePrivateKey)
        print(encryptedStr)

        # decriped
        rsaDecryptor = chilkat.CkRsa()
        success = rsaDecryptor.UnlockComponent("Anything for 30-day trial")
        if (success != True):
            print("RSA component unlock failed")
            sys.exit()

        privKey = chilkat.CkPrivateKey()

        success = privKey.LoadPemFile("C:\\Project\\testProgram\\IOT\\IOT\\firmwSign\\privatekey.pem")
        
        if (success != True):
            print(privKey.lastErrorText())
            sys.exit()
        print("Private Key from DER:")
        print(privKey.getXml())

        rsaDecryptor.put_EncodingMode("hex")
        success = rsaDecryptor.ImportPrivateKey(privKey.getXml())
        usePrivateKey = True
        decryptedStr = rsaDecryptor.decryptStringENC(encryptedStr,usePrivateKey)

        print(decryptedStr)

    except Exception as e:
        print("Error decoding certificate: {:}".format(e))


if __name__ == "__main__":
    print("Python {:s} on {:s}\n".format(sys.version, sys.platform))
    main()