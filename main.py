# -*- coding: utf-8 -*-
# @Time    : 11/8/19 3:08 PM
# @Author  : Alex Hu
# @Contact : jthu4alex@163.com
# @FileName: main.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0


from tornado.web import Application, RequestHandler, url
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from datetime import datetime
from random import randint
from tornado.escape import json_encode
import os
from DBAdaptor import DBAdaptor
import operator


# define global variable
define('port', default=8000, type=int, help='this is the port for application')

clients = set()

conn_redis = DBAdaptor('redis').get_conn()

data_last = None


class IndexHandler(RequestHandler):
    def get(self):
        # username = self.get_argument('username')
        # usernames = self.get_arguments('username')
        # self.write("<a href='" + self.reverse_url('login') + "'>login</a>")
        self.render('index.html')


class WSHandler(WebSocketHandler):
    def open(self):
        clients.add(self)

        # 向已在线用户发送消息
        for client in clients:
            remote_ip, port = self.request.connection.context.address
            now = datetime.now().strftime("%H:%M:%S")
            client.write_message("[{}][{}:{}]-进入".format(now, remote_ip, port))

    # 处理client发送的数据
    def on_message(self, message):
        print(message)
        # 将数据发送给当前连接的client
        # self.write_message(u"server said: " + message)
        # 将数据发送给所有连接的client
        for client in clients:
            client.write_message(u"server said: " + message)

    def on_close(self):
        print("WebSocket closed")
        clients.discard(self)

    # 允许所有跨域通讯，解决403问题
    def check_origin(self, origin):
        return True


def sendmsg_Ontime():
    global data_last
    gateway_id = str(1001)
    node_id = str(100002)
    if conn_redis.hlen(gateway_id + node_id):
        rsl = conn_redis.hgetall(gateway_id + node_id)
        print(rsl)
        if operator.ne(rsl, data_last):
            print('it is different than last')
            print(data_last)
            data_last = rsl
            print('data_last is: ', data_last)
    else:
        print('There is no data in redis.')
    # for client in clients:
    #     dt = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
    #     msg = {'dt': dt, 'data': {'tdt': dt, 'maxtc': randint(0, 9), 'gr': randint(0, 15), 'lc': randint(0, 20),
    #                               'lv': randint(0, 35), 'temp': randint(0, 30), 'humi': randint(0, 25), 'ev': randint(0, 40)}}
    #     client.write_message(json_encode(msg))


class ArticleHandler(RequestHandler):
    def initialize(self, title):
        print('-->initialize()')
        self.title = title

    def get(self):
        self.write('you are looking the article: %s' % self.title)


class LoginHandler(RequestHandler):
    def get(self):
        self.write('login show')

    def post(self):
        self.write('login handle')


if __name__ == '__main__':
    app = Application(
        [
            (r'/', IndexHandler),
            (r'/article', ArticleHandler, {'title': 'test title'}),
            url(r'/login', LoginHandler, name='login'),
            (r'/ws', WSHandler)
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True)
    http_server = HTTPServer(app)
    options.parse_command_line()

    http_server.bind(options.port)
    http_server.start()

    PeriodicCallback(sendmsg_Ontime, 2000).start()
    IOLoop.current().start()
