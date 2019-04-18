import subprocess
import os
subprocess.call('date')
folderpath = os.getcwd()
print("Current work directory is:"+str(folderpath))
print("Read the eeprom data.")
subprocess.call("sudo ./eepflash.sh -f=sense_read.eep -t=24c32 -r", shell=True)
print("Convert the *.eep file")
subprocess.call("./eepdump sense_read.eep eepData.txt",shell=True)
startPrint = False
with open('eepData.txt', 'r') as f:
    for line in f:
        if str(line).rstrip().strip() == 'dt_blob':
            startPrint = True
            subprocess.call('clear')
        if startPrint: print(line)

#from Crypto.PublicKey import RSA
#key = RSA.generate(1024)
#f = open("private.pem", "wb")
#f.write(key.exportKey('PEM'))
#f.close()

#pubkey = key.publickey()
#f = open("public.pem", "wb")
#f.write(pubkey.exportKey('OpenSSH'))
#f.close()
#!/usr/bin/env python

