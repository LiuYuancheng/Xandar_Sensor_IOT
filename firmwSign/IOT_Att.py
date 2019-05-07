import random,string
import os 
import mimetypes
from uuid import getnode as get_mac

global p,q,state
#extract specified length of bits
def bitExtracted(number, k, s):   
    return ( ((1 << k) - 1)  &  (number >> (s-1) ) )

#extract challenege response pair for the given key and iteration
def extract_CRpair(text):
	i=0
	final=bitExtracted(get_mac(),16,1) #UNIQUE PUFF VALUE FOR EACH DEVICE
	test=[(ord(k)^final) for k in text]	
	for k in test:
		if(i!=len(test)-1):
			test[i]=test[i]^test[i+1]
			final+=test[i]<<2
		else:
			final+=test[i]<<2
		i+=1	
	return final
def string_to_list(inputString):
    """Convert a string into a byte list"""
    return [ord(c) for c in inputString] #returns the corresponding unicode integer for the char for ex; a==97

def setKey(key,m):
    """RC4 Key Scheduling Algorithm (KSA)"""
    global p, q, state
    state = [n for n in range(m)] #fill with numnber ranging from 0 to 255
    #print state
    p = q = j = 0
    for i in range(m):
        j = (j + state[i] + key[i % len(key)]) % m
        state[i], state[j] = state[j], state[i]

def IOT_ATT(text, m, filePath):
	global p, q, state
	if not os.path.exists(filePath): 
		print("The file <%s> is not exist" %filePath)
		return None
	fh = open(filePath,"rb")
	setKey(string_to_list(text),m)
	cr_response=extract_CRpair(text)#P(C)
	init_cs=cr_response^m#sigma(0)<--p(c) xor x0
	print("xxxxxxxxxxx %s" %str(len(state)))
	pprev_cs=state[256]#c[(j-2)mod 8]
	prev_cs=state[257]#c[(j-1)mod 8]
	current_cs=state[258]#c[j]
	init_seed=m#set x(i-1)
	#print init_cs.bit_length(),bin(init_cs),init_cs
	for i in range(m):
		swatt_seed=cr_response^init_seed #y(i-1)=p(c) xor x(i-1)
		Address=(state[i]<<8)+prev_cs#(RC4i<<8)+c[(j-1)mod 8]
		'''use python PRG to generate address Range'''
		random.seed(Address)
		Address=random.randint(1,128000)
		'''read the EEPROM Memory content'''
		fh.seek(Address)
		strTemp = fh.read(1)
		'''calculate checksum at the location'''
		print("sssss%s" %str(strTemp))
		if not strTemp:
			continue
		#current_cs=current_cs+(ord(strTemp[0])^pprev_cs+state[i-1])
		current_cs=current_cs+(ord(strTemp)^pprev_cs+state[i-1])

		#extra seed for the SWATT
		init_seed=current_cs+swatt_seed
		#update current_cs
		current_cs=current_cs>>1
		#update c[(j-2)mod 8] & c[(j-1)mod 8]
		pprev_cs=prev_cs
		prev_cs=current_cs
	return hex(hash(current_cs))
		#current_cs=current_cs+


'''for m in range(1000):
	random.seed(1213)
	test=random.randint(11211,12321)'''	

