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
from tornado.escape import json_encode
import os
from DBAdaptor import db_factory
import operator


# define global variable
define('port', default=8000, type=int, help='this is the port for application')

clients = set()

conn_redis = db_factory.create_conn('redis')
conn_influxdb = db_factory.create_conn('influxdb')
conn_mysql = db_factory.create_conn('mysql')

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
    if conn_redis.get_conn().hlen(gateway_id + node_id):
        rsl_byte = conn_redis.get_conn().hgetall(gateway_id + node_id)
        rsl = {k.decode(): int(v.decode()) for k, v in rsl_byte.items()}
        print("get from redis ", rsl)
        if operator.ne(rsl, data_last):
            print('it is different than last')
            data_last = rsl
            dt = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
            msg = {'dt': dt, 'data': {'tdt': dt, 'maxtc': rsl['maxtc'], 'gr': rsl['gr'], 'lc': rsl['lc'],
                                      'lv': rsl['lv'], 'temp': rsl['temp'], 'humi': rsl['humi'], 'ev': rsl['ev']}}
            for client in clients:
                client.write_message(json_encode(msg))
    else:
        print('There is no data in redis.')


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


class HistoryDataHandler(RequestHandler):
    def get(self):
        dt_begin_str = self.get_argument('begin_dt', '')
        dt_end_str = self.get_argument('end_dt', '')
        var_id = self.get_argument('id', '1')
        times, datas, isdetail = self._select_databydt(dt_begin_str, dt_end_str, var_id)
        resp = {'gateway_id': '1001', 'node_id': '100002', 'time': times, 'datas': datas, 'isdetail': isdetail}
        self.write(resp)

    def _select_databydt(self, begindt_str, enddt_str, id):
        isdetail = True
        id_field_name = {1: 'gr', 2: 'lc', 3: 'lv', 4: 'temp', 5: 'humi', 6: 'ev', 7: 'maxtc'}
        field_name = id_field_name[int(id)]
        begindt = datetime.strptime(begindt_str, '%Y-%m-%d %H:%M:%S')
        enddt = datetime.strptime(enddt_str, '%Y-%m-%d %H:%M:%S')
        delta = enddt - begindt
        if delta.days < 1 and delta.seconds < 7200:
            tab_name = 'test_tab'
            sql = "select %s from %s where time >= '%s' and time <= '%s' tz('%s')" % (field_name, tab_name, begindt_str, enddt_str, 'Asia/Shanghai')
        else:
            isdetail = False
            tab_name = 'mean_min_max_1h'
            args = (field_name + '_mean', field_name + '_max', field_name + '_min') + (tab_name, begindt_str, enddt_str, 'Asia/Shanghai')
            sql = "select %s,%s,%s from %s where time >= '%s' and time <= '%s' tz('%s')" % args
        print(sql)
        rsl = conn_influxdb.exec_sql(sql)
        times = []
        datas = []
        if rsl:
            if isdetail:
                for r in rsl:
                    times.append(r['time'])
                    datas.append(r[field_name])
            else:
                for r in rsl:
                    times.append(r['time'])
                    data = {'mean': r[field_name + '_mean'], 'max': r[field_name + '_max'], 'min': r[field_name + '_min']}
                    print(data)
                    datas.append(data)
        return times, datas, isdetail



class NodeDataHandler(RequestHandler):
    def get(self):
        gateway_id = '1001'
        sql = 'select * from info_nodes where gateway_id=%s order by node_id' % gateway_id
        print(sql)
        rsl = conn_mysql.get_data(sql)
        print(rsl)
        if rsl:
            resp = {'datas': [{'id': r[0], 'node_id': r[1]} for r in rsl]}
        else:
            resp = {'datas': []}
        self.write(resp)


class VariableDataHandler(RequestHandler):
    def get(self):
        node_id = self.get_argument('node_id', '1')
        sql = 'select info_maptab_var_tabname.id,info_variable.name,info_maptab_var_tabname.tab_name from info_variable inner join info_maptab_var_tabname on(info_variable.id=info_maptab_var_tabname.variable_id) where node_id=%d' % int(node_id)
        rsl = conn_mysql.get_data(sql)
        print(rsl)
        if rsl:
            resp = {'datas': [{'id': r[0], 'var_name': r[1]} for r in rsl]}
        else:
            resp = {'datas': []}
        self.write(resp)


if __name__ == '__main__':
    settings = {
        'template_path': os.path.join(os.path.dirname(__file__), "templates"),
        'static_path': os.path.join(os.path.dirname(__file__), "static"),
        'debug': True,
    }

    app = Application(
        [
            (r'/', IndexHandler),
            (r'/article', ArticleHandler, {'title': 'test title'}),
            url(r'/login', LoginHandler, name='login'),
            (r'/ws', WSHandler),
            (r'/api/datas/history', HistoryDataHandler),
            (r'/api/datas/nodes', NodeDataHandler),
            (r'/api/datas/variables', VariableDataHandler),
        ],
        **settings)
    http_server = HTTPServer(app)
    options.parse_command_line()

    http_server.bind(options.port)
    http_server.start()

    PeriodicCallback(sendmsg_Ontime, 2000).start()
    IOLoop.current().start()
