#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import threading
import hashlib
'''
文件夹传输服务器端程序
传输协议：
1. 基于TCP协议；
2. 客户端连接服务器成功后，客户端不发送任何消息，服务器端首先将文件的描述信息
    （定长包头，长度为347B）发送给客户端，紧接着发送文件数据给客户端，
    发送文件数据后断开连接；
3. 文件描述信息结构为：文件相对发送文件夹的相对路径名（300B，右边填充空格，UTF-8编码）
    +文件大小（15B，右边填充空格）+ 文件MD5值（32B, 大写形式）
4. 若文件夹中有空文件夹，发送空文件夹时，文件描述信息为：空文件夹相对发送文件夹的相对路径名
    （300B，右边填充空格，UTF-8编码）
    +文件大小设为-1（15B，右边填充空格）+ 文件MD5值设为(' ' *32),即32个空格（32B, 大写形式）
'''

def get_file_md5(file_path):
    '''
    函数功能：生成发送文件的MD5
    参数描述：
        file_path 发送文件的路径

    '''
    m = hashlib.md5()

    with open(file_path, "rb") as f:
        while True:
            data = f.read(1024)
            if len(data) == 0:
                break    
            m.update(data)
    
    return m.hexdigest().upper()

def send_empty_dir(sock_conn, file_abs_path, dest_file_parent_path):
    '''
    函数功能：将目标文件夹中所含的空文件夹发送给客户端
    参数描述：
        sock_conn 套接字对象
        dir_abs_path 空文件夹文件的绝对路径
        dest_file_parent_path 待发送文件的文件目录的相对路径（相对于发送的文件夹）
    '''
    file_name = file_abs_path[len(dest_file_parent_path):] # 获取目标文件夹的名字
    # 切完后的file_name可能是这样的“\a”,在Linux下“/a”，去掉斜杠
    if file_name[0] == '\\' or file_name[0] == '/':
        file_name = file_name[1:]
    # 将空文件夹下的文件的大小设为-1，MD5设为32个空格    
    file_size = -1
    file_md5 = ' ' * 32
    # 根据传输协议，设置包头内容
    file_name = file_name.encode()
    file_name += b' ' * (300 - len(file_name))
    file_size = "{:<15}".format(file_size).encode()

    file_desc_info = file_name + file_size + file_md5.encode() #加码后的包头内容
    # 发送空文件夹的包头
    sock_conn.send(file_desc_info)
    
def send_one_file(sock_conn, file_abs_path, dest_file_parent_path):
    '''
    函数功能：将一个文件发送给客户端
    参数描述：
        sock_conn 套接字对象
        file_abs_path 待发送的文件的绝对路径
        dest_file_parent_path 待发送文件的文件目录的相对路径（相对于发送的文件夹）
    '''
    file_name = file_abs_path[len(dest_file_parent_path):] # 获取目标文件夹的名字
    # 切完后的file_name可能是这样的“\a”,在Linux下“/a”，去掉斜杠
    if file_name[0] == '\\' or file_name[0] == '/':
        file_name = file_name[1:]

    file_size = os.path.getsize(file_abs_path)
    file_md5 = get_file_md5(file_abs_path)
    # 将空文件夹下的文件的大小设为-1，MD5设为32个空格
    file_name = file_name.encode()
    file_name += b' ' * (300 - len(file_name))
    file_size = "{:<15}".format(file_size).encode()

    file_desc_info = file_name + file_size + file_md5.encode() #加码后的包头内容
    # 发送目标文件夹下发送文件的包头
    sock_conn.send(file_desc_info)
    # 变读取文件内容变发送
    with open(file_abs_path, "rb") as f:
        while True:
            data = f.read(1024)
            if len(data) == 0:
                break
            sock_conn.send(data)


def send_file_thread(sock_conn, dest_file_abs_path,dest_file_parent_path):
    '''
    函数功能：遍历目标文件夹下的子文件夹、以及所有文件，调用发送文件函数和发送空文件夹函数
    参数描述：sock_conn 连接套接字
             dest_file_abs_path 目标文件夹的绝对路径
             dest_file_parent_path 目标文件夹父目录的绝对路径
    '''
    try:
        for root, dirs, files in os.walk(dest_file_abs_path):
            # 如果是空文件夹，就掉用空文件夹发送函数
            if len(dirs) == 0 and len(files) ==0:
                send_empty_dir(sock_conn, root, dest_file_parent_path)
            # 如果有文件，就调用发送文件的函数
            for f in files:
                file_abs_path = os.path.join(root, f) # 获取文件的绝对路径
                print(file_abs_path)
                send_one_file(sock_conn, file_abs_path,dest_file_parent_path)
    except Exception as e:
        print(e)
    finally:
        sock_conn.close()


def main ():


    dest_file_abs_path = os.path.abspath(sys.argv[1]) # 获取当前用户输入（在终端中打开）的文件夹的绝对路径
    dest_file_parent_path = os.path.dirname(dest_file_abs_path) #获取目标文件夹的父目录的绝对路径


    # 绑定套接字，监听
    sock_listen = socket.socket()
    sock_listen.bind(("127.0.0.1", 9999))
    sock_listen.listen(5)

    while True:
        sock_conn, client_addr = sock_listen.accept()
        print(client_addr, "已连接！")
        # 调用发送的线程
        threading.Thread(target=send_file_thread, args=(sock_conn, dest_file_abs_path, dest_file_parent_path)).start()

    sock_listen.close()

if __name__ == "__main__":
    main()
