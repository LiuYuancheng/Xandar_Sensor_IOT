import sys
import socket


TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 20  # Normally 1024, but we want fast response


try:
    tcpSer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSer.bind((TCP_IP, TCP_PORT))
    tcpSer.listen(1)
except:
    print("TCP socket init error")
    raise

terminate = False

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
    except:
        continue