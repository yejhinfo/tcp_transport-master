import socket
import os
import hashlib
import time



'''
文件夹传输客户端程序
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

def get_file_md5(file_name_path):
    '''
    函数功能：将发送过来的文件生成MD5值
    参数描述：
        file_name_path 接收文件的绝对路径

    '''
    m = hashlib.md5()
    #print(file_name_path)
    with open(file_name_path, "rb") as f:
        while True:
            data = f.read(1024)
            if len(data) == 0:
                break    
            m.update(data)
    
    return m.hexdigest().upper()




def recv_file(sock):
    '''
    函数功能：根据协议循环接收包头，根据接收到的包头（文件描述信息结构）创建文件夹及其子文件夹，
             在相应目录下写入文件
    参数描述：
        sock 连接套接字

    '''
    while True:
        # 根据协议先接收文件名或空文件夹名的相对路径的字节
        file_name_path = sock.recv(300).decode().rstrip()
        #print(file_name_path)
        # 若文件名长度为0，说明接收文件夹完毕，跳出循环
        if len(file_name_path) == 0 : 
            break
        # 接收文件大小的字节
        file_size = sock.recv(15).decode().rstrip()
        # 若文件大小字节为'-1'，根据协议接收到的为空文件夹
        if int(file_size) == -1:
            print("成功接收空文件夹！{}".format(file_name_path))
            os.makedirs(file_name_path,exist_ok= True)
            continue # 继续循环
        # 若接收到的文件大小字节的长度为0，说明接收文件夹完毕，跳出循环
        if len(file_size) == 0:
            break
        #print(file_size)
        # 接收MD5字节，若长度为0，跳出循环
        file_md5 = sock.recv(32).decode().rstrip()
        if len(file_md5) == 0:
            break
        #print(file_md5)
        # 根据接收到的包头信息，创建文件夹
        os.makedirs(os.path.dirname(file_name_path), exist_ok=True)

        file_name = os.path.basename(file_name_path)
        # 根据文件大小循环接收并写入
        recv_size = 0
        start_time = time.time() 

        f = open(file_name_path, "wb")                                            #初始化已接收到的字节
        while recv_size < int(file_size):                             #若接收到的字节小于文件大小就循环接收，并写入本地
            file_data = sock.recv(int(file_size) - recv_size)
            if len(file_data) == 0:
                break

            f.write(file_data)            

            recv_size += len(file_data)
            print("\r正在接收{}文件，已接收{}字节".format(file_name, recv_size),end= ' ')
        f.close()

        end_time = time.time()
        t = end_time - start_time
        # 调用MD5生成函数检验收到的文件是否是发送方的原文件
        recv_file_md5 = get_file_md5(file_name_path)          
        if recv_file_md5 == file_md5:
            print("\n成功接收文件{},用时{:.2f}s\n".format(file_name, t))
        else:
            print("接收文件 %s 失败（MD5校验不通过）\n" % file_name)
            break


def main():
    server_ip = input("请输入目标主机地址：")
    server_port = int(input("请输入目标主机端口："))
    sock_bind = (server_ip, server_port)
    sock = socket.socket()
    sock.connect(sock_bind)
    os.chdir(r"C:\Download")        # 先进入所要接收文件夹的目录
    recv_file(sock)
    print("文件夹接收成功！")
    sock.close()

if __name__ == "__main__":
    main()
