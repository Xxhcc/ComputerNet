import socket
import struct
import time
import sys
import math

# 报文格式： Seq no两字节 Ver一字节 request_type一字节（用于表示发送请求的类型，在本实验中有建立连接：0，传输数据：1，断开连接：2,确认断开连接：3）

CLIENT_TIMEOUT = 0.1  # 超时时间，单位：秒
MAX_RETRANSMISSIONS = 2  # 最大重传次数
VERSION = 2  # 版本号
PAYLOAD = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'  # 无意义的数据作为有效载荷
PAYLOAD += b'\x00' * (199 - len(PAYLOAD))  # 不足199字节填充
POCKET_NUM = 12  # 传送包的数目
POCKET_LENGTH = 203  # 报文总长度203字节


def send_request(server_ip, server_port):
    first_response_time = -1
    last_response_time = -1
    send_pocket_num = 0  # 实际发送的包的数量

    # 创建UDP套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(CLIENT_TIMEOUT)

    flag = False
    # 建立连接 “三次握手”
    link_request = struct.pack('!HBB', 0, VERSION, 0) + PAYLOAD
    client_socket.sendto(link_request, (server_ip, server_port))
    try:
        response, server_address = client_socket.recvfrom(1024)
        seq_no, ver, sys_time, flag_no = struct.unpack('!HBQB', response[:12])
        if flag_no == 0 and ver == VERSION:
            flag = True
            first_response_time = sys_time
    except socket.error:
        flag = False

    # 成功建立连接
    if flag:
        # 初始化统计信息
        received_packets = 0
        rtt_all = []  # 用于存储RTT值

        # 发送请求并处理响应
        for sequence_number in range(1, POCKET_NUM + 1):
            for attempt in range(MAX_RETRANSMISSIONS + 1):
                # 请求报文
                message = struct.pack('!HBB', sequence_number, VERSION, 1) + PAYLOAD

                # 发送请求报文
                send_time = time.time() * 1000
                client_socket.sendto(message, (server_ip, server_port))
                send_pocket_num += 1
                # 等待服务器响应
                try:
                    response, server_address = client_socket.recvfrom(POCKET_LENGTH)
                    seq_no, ver, sys_time = struct.unpack('!HBQ', response[:11])
                    if seq_no == sequence_number and ver == VERSION:
                        receive_time = time.time() * 1000
                        rtt = receive_time - send_time  # 计算RTT（ms）
                        # 更新统计信息
                        received_packets += 1
                        rtt_all.append(rtt)  # 存储RTT值
                        # 打印接收到的响应信息
                        print(f"Sequence No: {sequence_number}, {server_ip}：{server_port}，RTT: {rtt:.2f}ms")
                        break  # 成功接收到响应，退出重传循环
                except socket.timeout:
                    # 发生超时，继续重传
                    if attempt < MAX_RETRANSMISSIONS:
                        print(f"Sequence No: {sequence_number}, Request Timeout")
                    else:
                        # 两次重传失败，不再重传
                        print(f"Sequence No: {sequence_number}, Give up retransmission")
                except socket.error:
                    print("服务器端未开启或异常关闭，请重新检查！")

        # 释放连接 “四次挥手”
        close_request = struct.pack('!HBB', 0, VERSION, 2) + PAYLOAD
        client_socket.sendto(close_request, (server_ip, server_port))
        response1, server_address1 = client_socket.recvfrom(POCKET_LENGTH)  # 第一次接收
        seq_no1, ver1, sys_time, flag_no1 = struct.unpack('!HBQB', response1[:12])
        response2, server_address2 = client_socket.recvfrom(POCKET_LENGTH)  # 第二次接收
        seq_no2, ver2, sys_time, flag_no2 = struct.unpack('!HBQB', response2[:12])
        if ver1 == ver2 == VERSION and flag_no1 == 2 and flag_no2 == 3:
            last_response_time = sys_time
            close_request = struct.pack('!HBB', 0, VERSION, 3) + PAYLOAD
            client_socket.sendto(close_request, (server_ip, server_port))
            client_socket.close()

        # 计算汇总信息
        if len(rtt_all) != 0:
            total_rtt = sum(rtt_all)
            loss_rate = (1 - received_packets / send_pocket_num) * 100
            max_rtt = max(rtt_all)
            min_rtt = min(rtt_all)
            rtt_std_dev = math.sqrt(sum([(rtt - sum(rtt_all) / len(rtt_all)) ** 2 for rtt in rtt_all]) / len(rtt_all))
            average_rtt = total_rtt / received_packets if received_packets > 0 else 0
        else:  # 所有数据报均未收到
            loss_rate = max_rtt = min_rtt = rtt_std_dev = average_rtt = 0

        if first_response_time != -1 and last_response_time != -1:
            total_response_time = last_response_time - first_response_time
        else:  # 服务器端一直未响应
            total_response_time = 0.00
        # 输出汇总信息
        print(f"接收到的udp packets数目: {received_packets}")
        print(f"丢包率: {loss_rate:.2f}%")
        print(f"最大RTT: {max_rtt:.2f}ms")
        print(f"最小RTT: {min_rtt:.2f}ms")
        print(f"平均RTT: {average_rtt:.2f}ms")
        print(f"RTT的标准差: {rtt_std_dev:.2f}ms")
        print(f"Server的整体响应时间: {total_response_time:.2f}ms")
    else:  # 连接建立失败
        print("连接建立失败，请重新建立连接！")
        # 关闭套接字
        client_socket.close()


# 主函数
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("输入参数为serverIp和serverPort！")
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])
    send_request(ip, port)
