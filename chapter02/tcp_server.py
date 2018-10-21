#coding=utf-8

import socket
import threading

bind_ip =  "0.0.0.0"
bind_port = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((bind_ip, bind_port))

server.listen(5)

print("[*] Listening on {0}:{1}".format(bind_ip, bind_port))

#client task threading
def handle_client(client_socket):
    #print client data
    request = client_socket.recv(1024)
    print("[*] Received: {}".format(request))
    client_socket.send("ASK!")
    client_socket.close()

while True:
    client,  addr = server.accept()
    print("[*] Accept connection from: {0}:{1}".format(addr[0], addr[1]))

    #threading
    client_handle = threading.Thread(target = handle_client, args = (client, ))
    client_handle.start()
