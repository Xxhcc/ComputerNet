import socket
import struct
import random
import sys

FILENAME = "message.txt"
REVFILENAME = "messagerev.txt"


def handle_messages(client_socket, block_lens):
    count = 0
    try:
        # 发送data，接收reverse_data
        with open(FILENAME, 'rb') as rfile, open(REVFILENAME, 'w') as wfile:
            for block_len in block_lens:
                # 发送reverseRequest报文
                req_type = 3
                data = rfile.read(block_len)
                req_mess = struct.pack('!HI', req_type, block_len) + data
                client_socket.sendall(req_mess)

                # 接收reverseAnswer报文
                res_mess = client_socket.recv(1024)
                if len(res_mess) < 6:  # 长度没有达到reverseAnswer报文的长度
                    continue
                res_type, s_len = struct.unpack('!HI', res_mess[:6])
                if res_type == 4 and len(res_mess) >= 6 + s_len:  # 判断reverse_data部分是否完整
                    count += 1
                    message = res_mess[6:6 + s_len].decode("utf-8")
                    print(f"第{count}块：{message}")
                    wfile.write(message + "\n")  # 将收到的反转文本存入文件

        # 输出全部反转文本
        with open(REVFILENAME, 'r') as file:
            print(file.read())
    except socket.error:
        print("服务器端异常关闭，请重新检查！")
        return


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("输入参数依次为为serverIp、serverPort、Lmin和Lmax！")
        sys.exit(1)

    # 获取用户输入
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    L_MIN = int(sys.argv[3])
    L_MAX = int(sys.argv[4])

    # 创建TCP套接字
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        client_socket.settimeout(5)  # 设置超时时间为5秒
    except socket.error:
        print(f"服务器端({server_ip}:{server_port})未开启或异常关闭，请重新检查！")
        sys.exit(1)

    # 读取文件长度
    with open(FILENAME, 'rb') as file:
        file_len = len(file.read())

    # 如果文件长度无法满足要求，则给出提示并退出
    if file_len < L_MIN:
        print(f"文件总长度为{file_len}，您输入的Lmin值太大，请重新输入！")
        client_socket.close()
        sys.exit(1)

    # 随机生成不同的块长
    block_lens = []  # 存储随机生成的块长
    m = file_len
    while m > 0:
        length = random.randint(L_MIN, L_MAX)
        if m >= length:
            block_lens.append(length)
            m -= length
        else:
            block_lens.append(m)
            m = 0

    N = len(block_lens)  # 总块数
    link_flag = False  # 用于标识是否成功建立连接

    # 发送Initialization报文 + 接收agree报文
    try:
        request_type = 1
        request = struct.pack('!HI', request_type, N)  # 发送Initialization报文
        client_socket.send(request)
        response = client_socket.recv(1024)  # 接收agree报文
        response_type = struct.unpack('!H', response[:2])[0]
        if response_type == 2:
            link_flag = True
    except socket.error:
        print(f"服务器端({server_ip}:{server_port})未开启或异常关闭，请重新检查！")
        client_socket.close()
        sys.exit(1)

    # 成功建立连接
    if link_flag:
        print("已经成功与服务器建立连接")
        handle_messages(client_socket, block_lens)
    else:
        print("未收到服务器端回应，请重新建立连接！")
        client_socket.close()
        sys.exit(1)

    # 关闭套接字
    client_socket.close()
