# -*- coding: utf-8 -*-
# @Time    : 11/11/19 1:31 PM
# @Author  : Alex Hu
# @Contact : jthu4alex@163.com
# @FileName: Server.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0

import socketserver
import pika
import datetime


class MyTCPHandler(socketserver.BaseRequestHandler):
    data = None

    def handle(self):
        try:
            while True:
                self.data = self.request.recv(1024)
                print(datetime.datetime.now().time(), " {} send:".format(self.client_address), self.data)
                print(type(self.data))
                channel.basic_publish(exchange='', routing_key='test', body=self.data)
                if not self.data:
                    print("connection lost")
                    break
                self.request.sendall(self.data.upper())
        except Exception as e:
            print(self.client_address, "连接断开")
        finally:
            self.request.close()

    def setup(self):
        print("before handle,连接建立：", self.client_address)

    def finish(self):
        print("finish run  after handle")


def init_rabbitmq():
    username = 'Alex'
    pwd = 'Alex11235813'
    user_pwd = pika.PlainCredentials(username, pwd)
    s_conn = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=user_pwd))
    channel = s_conn.channel()
    channel.queue_declare(queue='test')
    return channel


channel = init_rabbitmq()


if __name__ == '__main__':
    HOST, PORT = "", 8808

    server = socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler)  #多线程版
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        channel.close()
