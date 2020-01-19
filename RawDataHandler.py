# -*- coding: utf-8 -*-
# @Time    : 12/5/19 5:01 PM
# @Author  : Alex Hu
# @Contact : jthu4alex@163.com
# @FileName: RawDataHandler.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0

import pika
import binascii
import datetime
from config import config_parser as cper
from DBAdaptor import db_factory
import operator


class RawDataHandler(object):
    """
    here need factory model
    """
    def __init__(self, need_save=False):
        self.channel = self.__init_rabbitmq()
        self.channel.basic_consume('test', self.__callback, True)
        self.redis = db_factory.create_conn('redis')
        self.influxdb = db_factory.create_conn('influxdb')
        self.data_last = None
        self.need_save = need_save

    def __init_rabbitmq(self):
        conf = cper.read_yaml_file('rabbitmq')
        host = conf['host']
        username = conf['username']
        pwd = conf['pwd']
        user_pwd = pika.PlainCredentials(username, pwd)
        s_conn = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=user_pwd))
        channel = s_conn.channel()
        channel.queue_declare(queue='test')
        return channel

    def __callback(self, ch, method, properties, body):
        print('got data: ', body)
        gateway_id = str(int.from_bytes(body[:2], 'big'))
        print('Gateway ID: ', gateway_id)
        node_id = str(int.from_bytes(body[2:6], 'big'))
        print('Node ID: ', node_id)
        tdt_str = binascii.b2a_hex(body[6:12]).decode()
        tdt = datetime.datetime.strptime(tdt_str, '%y%m%d%H%M%S')
        print('tdt: ', tdt)
        maxtc = int.from_bytes(body[12:14], 'big')
        print('maxtc: ', maxtc / 10)
        gr = int.from_bytes(body[14:16], 'big')
        lc = int.from_bytes(body[16:18], 'big')
        lv = int.from_bytes(body[18:20], 'big')
        temp = int.from_bytes(body[20:22], 'big')
        humi = int.from_bytes(body[22:23], 'big')
        ev = int.from_bytes(body[23:25], 'big')
        print('gr: ', gr / 1000)
        print('lc: ', lc / 100)
        print('lv: ', lv / 100)
        print('temp: ', temp / 10)
        print('humi: ', humi, '%')
        print('ev: ', ev / 10)
        data = [
            {
                'measurement': 'test_tab',
                'time': datetime.datetime.utcfromtimestamp(tdt.timestamp()).isoformat(),
                'tags': {
                    'gateway_id': gateway_id,
                    'node_id': node_id
                },
                'fields': {
                    'maxtc': maxtc,
                    'gr': gr,
                    'lc': lc,
                    'lv': lv,
                    'temp': temp,
                    'humi': humi,
                    'ev': ev
                }
            }
        ]
        if self.need_save:
            self.influxdb.saveall(data=data)
        values = {'maxtc': maxtc,
                  'gr': gr,
                  'lc': lc,
                  'lv': lv,
                  'temp': temp,
                  'humi': humi,
                  'ev': ev}
        if operator.ne(values, self.data_last):  # change the redis while the values is different
            self.data_last = values
            rsl = self.redis.get_conn().hmset(str(gateway_id) + str(node_id), values)
            if not rsl:
                print('ERROR! Fail to refresh redis.')

    def start(self):
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.close()


if __name__ == '__main__':
    handler1 = RawDataHandler(need_save=True)
    handler1.start()
