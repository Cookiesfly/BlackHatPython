#!/usr/bin/env python
# -*- code: utf-8 -*-

import sys
import socket
import getopt
import threading
import subprocess
#import logging  #没跑通，加日志调试

# 定义一些全局变量
listen = False   # 如True，启动监听相当于server，否则为client
command = False   # 是否建立shell
upload = False   # 是否上传
execute = ""   # 目标主机上执行的命令
target = ""   # 目标主机
upload_destination = ""   # 数据传输的目标文件
port = 0   # 目标端口

def usage():
    print("Netcat Tool")
    print()
    print("Usage: netcat.py -t target_host -p port")
    print("-l --listen              - listen on [host]:[port] for incoming connections")
    print( "-e --execute=file_to_run -execute the given file upon receiving a connection")
    print("-c --command             - initialize a commandshell")
    print("-u --upload=destination  - upon receiving connection upload a file and write to [destination]")
    print()    
    print("Examples:")
    print("netcat.py -t 192.168.0.1 -p 5555 -l -c")
    print("netcat.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("netcat.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | python ./netcat.py -t 192.168.11.12 -p 135")
    sys.exit(0)

# 客户端发送消息-->服务端，并接收服务端的回馈消息
def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到目标主机
        client.connect((target, port))
        #logging.info('目标主机   {0}{1}'.format(target, port))

        #encode()?
        if len(buffer):
            client.send(buffer.encode("utf-8"))

        while True:
            # 等待数据回传
            revc_len = 1
            response =  ""
            
            # s.recv(bufsize[,flag])用于获取缓冲中的数据，flag参数socket.MSG_WAITALL表示recv函数获取到指定size才会返回
            # 当客户端需要读取大量数据时，需要多次recv()
            while revc_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode("utf-8")

                # 表示数据已经接受完毕
                if recv_len < 4096:
                    break

            print(response, end=" ")

            # 等待更多输入
            buffer = input("")
            buffer += "\n"

            client.send(buffer.encode())

    except:
        print("[*] Exception! Exiting.")

    finally:
        client.close()

def run_command(command):
    # 处理换行符
    command = command.rstrip()

    # 执行命令并返回输出
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to excute command.\r\n"

    return output

# 服务端线程，处理客户端的连接任务
def client_handler(client_socket):
    global upload
    global execute
    global command

    # 检测是否设置为接收文件
    if len(upload_destination):

        # 读取所有字符并写下目标
        file_buffer = ""

        # 持续读取数据，直到没有符合的数据
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # 接受数据并将它们写到upload_destination
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # 确认文件已写
            client_socket.send("Successfully saved file to {}\r\n".format(upload_destination))
        except:
            client_socket.send("Failed to saved file to {}\r\n".format(upload_destination))

    # 检查需要执行的命令
    if len(execute):
        # 执行命令
        output = run_command(execute)

        client_socket.send(output)

    # 如果需要一个命令行shell，则进入另一个循环
    if command:
        while True:
            # 一个简单的窗口
            client_socket.send("<Netcat:#>".encode())

            # 现在接受数据直到发现换行符
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024).decode("utf-8")

            # 返还命令输出
            response = run_command(cmd_buffer)
            # 返回响应数据
            client_socket.send(response)

# 服务端监听客户端发起的连接，根据情况创建子线程处理
def server_loop():
    global target
    global port

    #如果没有定义target，则监听所有接口
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # 分拆一个线程处理新的client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

    

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # 读取命令行
    try:
        # sys.argv[1:] 过滤掉第一个参数
        # (":", "=")表示该选项必须有附加的参数
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu", ["help", "listen", "execute", \
                                                                "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
    
    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--excute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a    
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    # 是监听还是仅从标准输入发送数据？
    if not listen and len(target) and port > 0:
        # 从命令行读取内存数据
        buffer = sys.stdin.read()
        client_sender(buffer)

    if listen:
        server_loop()

main()