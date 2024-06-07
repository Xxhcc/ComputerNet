import socket
import struct
import threading

# 自定义常量
LINK_MAX = 10  # 最大接入客户端数量


def handle_request(client_socket, client_addr):
    request_num = 0  # 初始化请求反转字符串数量为0
    count = 0
    client_socket.settimeout(5)  # 设置超时时间为5秒
    while True:
        try:
            request = client_socket.recv(1024)
            if len(request) < 2:  # 数据报长度不足两字节
                continue

            request_type = struct.unpack('!H', request[:2])[0]  # 获取请求类型
            if request_type == 1:  # 收到Initialization报文
                if len(request) < 6:  # 长度没有达到Initialization报文的长度
                    continue
                _, request_num = struct.unpack('!HI', request[:6])  # 记录请求反转的字符串数量
                print(f"客户端{client_addr}成功建立连接，请求反转{request_num}块文本")

                # 发送agree报文
                response_type = 2
                response = struct.pack('!H', response_type)
                client_socket.send(response)
            elif request_type == 3:  # 收到reverseRequest报文
                if len(request) < 6:  # 长度没有达到reverseRequest报文的长度
                    continue
                _, s_len = struct.unpack('!HI', request[:6])  # 获取待反转文本长度
                if len(request) < 6 + s_len:  # data部分长度不足
                    continue

                count += 1
                s = request[6:6 + s_len].decode("utf-8")  # 获取data

                # 发送reverseAnswer报文
                s = s[::-1]  # 反转字符串
                response_type = 4
                response = struct.pack('!HI', response_type, s_len) + s.encode("utf-8")
                client_socket.send(response)
                if count == request_num:  # 处理文本块数达标
                    print(f"已与客户端{client_addr}断开连接，且请求处理完毕")
                    break
            else:  # 非已知类型报文，舍弃
                continue
        except socket.timeout:
            continue
        except socket.error:  # 客户端异常断开
            print(f"客户端{client_addr}异常断开连接，请重新检查")
            return


# 主函数
if __name__ == "__main__":
    server_ip = '192.168.47.129'  # 服务器IP地址
    server_port = 20000  # 服务器端口

    # 创建TCP套接字并绑定到指定IP地址和端口
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(LINK_MAX)

    # 监听客户端的接入
    print("Server started, listening on port：20000")
    while True:
        try:
            client_socket, client_addr = server_socket.accept()  # 实现多个客户端的接入
            client_handler = threading.Thread(target=handle_request, args=(client_socket, client_addr))
            client_handler.start()
        except socket.timeout:
            # 一定时间内没有用户接入，继续监听
            continue

    # 关闭套接字
    server_socket.close()
