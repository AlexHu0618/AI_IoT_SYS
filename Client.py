# -*- coding: utf-8 -*-
# @Time    : 11/11/19 1:35 PM
# @Author  : Alex Hu
# @Contact : jthu4alex@163.com
# @FileName: Client.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0

import socket
import time
import datetime
import binascii
import random


client = socket.socket()

# client.connect(('39.108.137.187', 8808))
client.connect(('127.0.0.1', 8808))

def run():
    while True:
        # cmd = input("(quit退出)>>").strip()
        # if len(cmd) == 0:
        #     continue
        # if cmd == "quit":
        #     break
        # client.send(cmd.encode())
        # cmd_res = client.recv(1024)
        # print(cmd_res.decode())
        try:
            client.send(send_byte())
            time.sleep(10)
        except KeyboardInterrupt as e:
            break

    client.close()


def send_byte():
    gw_id = (1001).to_bytes(length=2, byteorder='big', signed=False)
    node_id = (100002).to_bytes(length=4, byteorder='big', signed=False)
    dtnow_str = datetime.datetime.strftime(datetime.datetime.now(), '%y%m%d%H%M%S')
    tdt = binascii.a2b_hex(dtnow_str)  # BCD encode
    maxtc = (102 + random.randint(-10, 10)).to_bytes(length=2, byteorder='big', signed=False)
    gr = (50 + random.randint(-10, 10)).to_bytes(length=2, byteorder='big', signed=False)
    lc = (5 + random.randint(1, 5)).to_bytes(length=2, byteorder='big', signed=False)
    lv = (5 + random.randint(1, 5)).to_bytes(length=2, byteorder='big', signed=False)
    temp = (20 + random.randint(-10, 10)).to_bytes(length=2, byteorder='big', signed=False)
    humi = (80 + random.randint(-10, 10)).to_bytes(length=1, byteorder='big', signed=False)
    ev = (102 + random.randint(-10, 10)).to_bytes(length=2, byteorder='big', signed=False)
    temp1 = gw_id + node_id + tdt + maxtc + gr + lc + lv + temp + humi + ev
    cmd = bytearray(temp1)
    print(datetime.datetime.now(), ': ', cmd)
    return cmd


if __name__ == '__main__':
    run()
