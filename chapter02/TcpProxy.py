#!/usr/bin/env python3
# -*- code: utf-8 -*-

import sys
import socket
import threading

def hexdump(src, length=16):
    result = []
    # Python3中unicode类型重命名为str
    digits = 4 if isinstance(src, str) else 2

    # Python3中range替代xrange
    for i in range(0, len(src), length):
        s = src[i:i+length]
        # %-*s 代表输入一个字符串，- 号代表左对齐、后补空白，* 号代表对齐宽度由输入时确定
        # %*s 代表输入一个字符串，右对齐、前补空白，* 号代表对齐宽度由输入时确定
        # %04X 代表输入一个数字，按 16 进制打印，4 个字节对齐，前补 0
        hexa = ' '.join(["%0*X" % (digits, ord(x)) for x in s])
        text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.' for x in s])
        result.append("%04X    %-*s    %s" % (i, length*(digits + 1), hexa, text))

    # for i in range(0, len(src), length):
    #     s = src[i:i + length]
    #     hexa = ' '.join([hex(x)[2:].upper().zfill(digits) for x in s])
    #     text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.' for x in s])
    #     result.append("{0:04X}".format(i) + ' '*3 + hexa.ljust(length * (digits + 1)) + ' '*3 + "{0}".format(text))

    print("\n".join(result))

# 从一个连接中接收数据并返回
def receive_from(connection):
    buffer = ""

    # 此处设置了2s的超时，这取决于目标的情况
    connection.settimeout(2)

    try:
        while True:
            data = connection.recv(4096)

            if not data:
                break
            buffer += data
    except:
        pass
    return buffer

# 对目标是远程主机的请求进行修改
def request_handler(buffer):
    # 此处可以添加包修改代码
    return buffer

# 对目标是本地主机的响应进行修改
def response_handler(buffer):
    # 执行包修改
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # 连接远程主机
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # 如果必要从远程主机接受数据
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        # 发送给响应处理        
        remote_buffer = response_handler(remote_buffer)

        # 如果有数据传送给本地客户端，则发送它
        if len(remote_buffer):
            print("[<==] Sending {} bytes to localhost.".format(len(remote_buffer)))
            client_socket.send(remote_buffer)

        # 从本地循环读取数据，发送给远程主机和本地主机
        while True:
            # 从本地读取数据
            local_buffer = receive_from(client_socket)

            if len(local_buffer):
                print("[==>] Receive {} bytes from loaclhost.".format(len(local_buffer)))
                hexdump(local_buffer)

                # 发送给我们的本地请求
                local_buffer = request_handler(local_buffer)

                # 向远程主机发送数据
                remote_socket.send(local_buffer)
                print("[==>] Send to remote.")
            
            # 接收响应的数据
            remote_buffer = receive_from(remote_socket)

            if len(remote_buffer):
                print("[<==] Receive {} bytes from remote.".format(len(remote_buffer)))
                hexdump(remote_buffer)

                # 发送到响应处理函数
                remote_buffer = response_handler(remote_buffer)

                # 将响应发送给本地socket
                client_socket.send(remote_buffer)

                print("[<==] Sent to localhost.")

            # 如果两边都无数据，关闭连接
            if not len(local_buffer) or not len(remote_buffer):
                client_socket.close()
                remote_socket.close()
                print("[*] No more data. Closing connections.")

                break

def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except:
        print("[!!] Failed to listen on {}:{}".format(local_host, local_port))
        print("[!!] Check for another listening sockets or correct permissions.")
        sys.exit(0)

    print("[*] Listening on {}:{}".format(local_host, local_port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # 打印本地连接信息
        print("[==>] Received incoming connection from {}:{}".format(addr[0], addr[1]))
        
        # 开启一个线程与远程主机通信
        proxy_thread = threading.Thread(target=proxy_handler, args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()


def main():
    if len(sys.argv[1:]) != 5:
        print("Usege: ./proxy.py [localhost] [localport] [remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)

    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    # 告诉代理在发送给远程主机之前的连接和接受数据
    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False
    
    # 设置监听的socket
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

main()
    