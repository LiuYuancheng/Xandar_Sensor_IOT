import sys
import socket


TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 20  # Normally 1024, but we want fast response

CERT_PATH = "C:\\Project\\testProgram\\IOT\\IOT\\firmwSign\\publickey.cer"


try:
    tcpSer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSer.bind((TCP_IP, TCP_PORT))
    tcpSer.listen(1)
except:
    print("TCP socket init error")
    raise

terminate = False

def checkLogin(userName, password):
    return userName == '123' and password == '123'

while not terminate:
    # Add the reconnection handling
    try:
        conn, addr = tcpSer.accept()
        print('Connection address:'+str(addr))
        while not terminate:
            data = conn.recv(BUFFER_SIZE)
            if not data: break # get the ending message. 
            print("received data:"+str(data))
            if data == b'login':
                conn.send(b'Done')
            elif data == b'Fetch':
                f_send = "publickey.cer"
                with open(f_send, "rb") as f:
                    data = f.read()
                    sys.getsizeof(data)


                    conn.sendall(data)
            else:
                dataStr= data.decode('utf-8')

                args =  dataStr.split(';')
                tag = args[0]
                if tag == 'L':
                    if checkLogin(args[1], args[2]):
                        # send the cer file for sign the file: 
                        conn.send(b'Done')
                    else:
                        conn.send(b'Fail')
    except:
        continue