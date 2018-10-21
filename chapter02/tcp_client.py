#coding=utf-8
import socket

#target_host = "127.0.0.1"
#target_port = 9999
target_host = "www.baidu.com"
target_port = 80

# 三个假设： 1.连接总能成功 2.client首先发送数据 3.server每次及时响应

# create a socket poj
# AF_INET : ipv4    SOCK_STREAM : tcp
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect client
client.connect((target_host, target_port))

# send data(windows:\r\n  linux:\n)
# client.send("GET / HTTP/1.1\r\nHost: " + str(target_host) + "\r\n\r\n")
# TypeError: a bytes-like object is required, not 'str'
client.send(("GET / HTTP/1.1\r\nHost: " + str(target_host) + "\r\n\r\n").encode())

# recive data
response = client.recv(4096)

print(response)
