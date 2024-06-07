import socket
import struct
import time
import random

# 报文格式：Seq no两字节 Ver一字节 System time八字节 response_type一字节：用来标识对建立连接/接收到信息/断开连接的回应,请求 0/1/2,3

VERSION = 2  # 版本号
PAYLOAD = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'  # 无意义的字母序列
PAYLOAD += b'\x00' * (191 - len(PAYLOAD))  # 不足191字节填充
POCKET_LENGTH = 203  # 报文总长度203字节
DEFINE_LOSS_RATE = 0.3  # 自定义丢包率为30%


def handle_request(request, client_address):
    try:
        # 解析请求报文
        sequence_number, ver, request_type = struct.unpack('!HBB', request[:4])

        # 检查版本号
        if ver == VERSION:
            system_time = int(time.time() * 1000)  # 计算时间戳
            if request_type == 0:  # 请求类型为建立连接
                # 发送响应报文
                print(f"已经建立与客户端{client_address}的连接")
                response = struct.pack('!HBQB', sequence_number, ver, system_time, request_type) + PAYLOAD
                server_socket.sendto(response, client_address)
            elif request_type == 2:  # 请求类型为断开连接
                # 发送响应报文
                response1 = struct.pack('!HBQB', sequence_number, ver, system_time, request_type) + PAYLOAD
                server_socket.sendto(response1, client_address)
                # 发送响应报文
                request_type += 1
                response2 = struct.pack('!HBQB', sequence_number, ver, system_time, request_type) + PAYLOAD
                server_socket.sendto(response2, client_address)
            elif request_type == 3:  # 接受到client端的最后一个ack
                print(f"已经断开与客户端{client_address}的连接")
            else:  # 请求类型为传输数据
                # 模拟丢包，概率为30%
                if random.random() < DEFINE_LOSS_RATE:
                    return
                # 发送响应报文
                response = struct.pack('!HBQB', sequence_number, ver, system_time, request_type) + PAYLOAD
                server_socket.sendto(response, client_address)

    except socket.error:
        print("客户端异常关闭")


# 主函数
if __name__ == '__main__':
    server_ip = '192.168.47.129'  # 服务器IP地址
    server_port = 20000     # 服务器端口

    # 创建UDP套接字并绑定到指定IP地址和端口
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))

    # 监听客户端请求
    print(f"Server listening on {server_ip}:{server_port}")
    while True:
        try:
            request, client_address = server_socket.recvfrom(1024)

            # 处理请求信息
            handle_request(request, client_address)
        except socket.timeout:
            # 一定时间内没有收到数据包，继续监听
            continue

    # 关闭套接字
    server_socket.close()
