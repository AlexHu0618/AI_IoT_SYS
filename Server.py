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
import hmac
import os
from DBAdaptor import db_factory
from config import config_parser as cper
import pickle
import re


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
        1、加密验证授权连接（只允许我们的tcp client连接）；
        2、获取gateway_id判断是哪个用户的设备，（在平台注册设备时需要填入该gateway_id绑定用户，这里以mac代替）;
    """
    clients = {}

    def handle(self):
        try:
            while True:
                self.data = self.request.recv(1024)
                print(self.data)
                data_recv = eval(str(self.data, encoding='utf-8'))
                print(data_recv)
                if data_recv['type'] == 2:  # data or info: 1-data; 2-info.
                    if data_recv['status'] == 1:  # info data: 0-stop;1-start;2-quit;
                        self.dt_start = datetime.datetime.now()
                        print('start')
                    elif data_recv['status'] == 0:
                        self.dt_end = datetime.datetime.now()
                        print('stop')
                    elif not data_recv:
                        self.dt_end = datetime.datetime.now()
                        print('quit')
                        break
                    else:
                        break
                elif data_recv['type'] == 1:  # data
                    data_recv['gateway_id'] = self.gateway_id
                    # push to RabbitMQ, just MQ but not p/b
                    data = pickle.dumps(data_recv)
                    channel.basic_publish(exchange='', routing_key='gateway', body=data)
                else:
                    print("It is the wrong data frame!")
        except Exception as e:
            print(e)
            print(self.data)
            print(self.client_address, "连接断开")
            self.dt_end = datetime.datetime.now()
        finally:
            pass

    def setup(self):
        self.clients[self.request] = self.client_address
        if self.__auth_handler():
            print("Success to authorize before handling,连接建立：", self.client_address)
            self.request.sendall(b'success')
            if self.__judge_registered_gateway_id():
                print("The gateway_id is registered：", self.client_address)
                self.request.sendall(b'success')
                self.dt_accessed = datetime.datetime.now()
                self.__set_redis()
            else:
                print('Not registered gateway_id, closing conn')
                self.request.sendall(b'failed')
                self.finish()
        else:
            print('Fail to authorize, closing conn')
            self.request.sendall(b'failed')
            self.finish()

    def finish(self):
        print("finish run  after handle", self.client_address)
        self.dt_lost = datetime.datetime.now()
        print('dt_accessed: ', self.dt_accessed)
        print('dt_start: ', self.dt_start)
        print('dt_end: ', self.dt_end)
        print('dt_lost: ', self.dt_lost)
        self.clients.pop(self.request)
        print('the remaining clients: ', self.clients)

    def __auth_handler(self):
        print('start to authorize')
        msg = os.urandom(32)
        self.request.sendall(msg)
        h = hmac.new(secret_key, msg)
        digest = h.digest()
        response = self.request.recv(len(digest))
        return hmac.compare_digest(digest, response)

    def __judge_registered_gateway_id(self):
        print('Gateway-id is registered?....')
        msg = b'gateway_id'
        self.request.sendall(msg)
        response = self.request.recv(100)
        print('mac: ', response)
        # verify gateway_id from MySQL
        sql = "SELECT gateway_id,df_struct,table_name FROM info_gateway_node WHERE gateway_id='%s'" % str(response, encoding='utf-8')
        rsl = mysql.get_data(sql=sql)
        print(rsl)
        if rsl:
            self.gateway_id = rsl[0][0]
            self.df_struct = rsl[0][1]
            self.table_name = rsl[0][2]
            return True
        else:
            return False

    def __set_redis(self):
        """
        1\ get data from mysql
        2\ set something about the current gateway_id
        :return:
        """
        if self.gateway_id:
            frame_str = re.split(',', self.df_struct)
            frame = list(map(int, frame_str))
            sql = "SELECT map_treenode_var.id,info_variable.type FROM map_treenode_var INNER JOIN info_variable ON map_treenode_var.variable_id = info_variable.id WHERE map_treenode_var.id IN " + str(tuple(frame))
            rsl = mysql.get_data(sql=sql)
            if rsl:
                data = {'table_name': self.table_name, 'df_struct': self.df_struct, 'id_size': str(rsl)}
                redis.hmset(self.gateway_id, data)


def init_rabbitmq():
    conf = cper.read_yaml_file('rabbitmq')
    host = conf['host']
    username = conf['username']
    pwd = conf['pwd']
    user_pwd = pika.PlainCredentials(username, pwd)
    s_conn = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=user_pwd))
    channel = s_conn.channel()
    channel.queue_declare(queue='gateway')
    return channel


channel = init_rabbitmq()
mysql = db_factory.create_conn('mysql')
redis = db_factory.create_conn('redis').get_conn()


if __name__ == '__main__':
    HOST, PORT = "", 8809
    secret_key = b"!QAZ2wsx--Alex0618's screct"
    print('server is starting....')

    server = socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler)  # 多线程版
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        channel.close()
        server.shutdown()
        print('\nclosed')
        exit()
