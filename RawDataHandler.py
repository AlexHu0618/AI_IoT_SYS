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
import pickle


class RawDataHandler(object):
    """
    here need factory model
    从Redis中获取不同的网关ID对应的数据帧结构以及存储数据所需要的一切参数
    """
    def __init__(self, need_save=False):
        queue_name = 'gateway'
        self.channel = self.__init_rabbitmq(queue_name)
        self.channel.basic_consume(queue_name, self.__callback, True)
        self.redis = db_factory.create_conn('redis').get_conn()
        self.influxdb = db_factory.create_conn('influxdb')
        self.data_last = None
        self.need_save = need_save

    def __init_rabbitmq(self, queue):
        conf = cper.read_yaml_file('rabbitmq')
        host = conf['host']
        username = conf['username']
        pwd = conf['pwd']
        user_pwd = pika.PlainCredentials(username, pwd)
        s_conn = pika.BlockingConnection(pika.ConnectionParameters(host=host, credentials=user_pwd))
        channel = s_conn.channel()
        channel.queue_declare(queue=queue)
        return channel

    def __callback(self, ch, method, properties, body):
        data = pickle.loads(body)
        print('got data: ', data)
        gateway_id = data['gateway_id']
        if self.redis.exists(gateway_id):
            rsl = self.redis.hgetall(gateway_id)
            value = {k.decode(): v.decode() for k, v in rsl.items()}
            print(value)
            print(type(value))
            df_struct = list(map(int, value['df_struct'].split(',')))
            id_size = tuple(eval(value['id_size']))
            print(gateway_id)
            print(df_struct)
            print(id_size)
            rawdata = data['data_frame']
            map(float, rawdata)
            print(rawdata)
            min_num = min(len(df_struct), len(rawdata))
            points = []
            for index in range(min_num):
                point = {
                    'measurement': 'm_' + str(gateway_id),
                    'tags': {
                        'map_tv_id': df_struct[index]
                    },
                    'fields': {
                        'value': rawdata[index]
                    }
                }
                points.append(point)
            if points:
                self.influxdb.saveall(data=points)
        else:
            print('No key %s in Redis!' % gateway_id)
        # gateway_id = str(int.from_bytes(body[:2], 'big'))
        # print('Gateway ID: ', gateway_id)
        # node_id = str(int.from_bytes(body[2:6], 'big'))
        # print('Node ID: ', node_id)
        # tdt_str = binascii.b2a_hex(body[6:12]).decode()
        # tdt = datetime.datetime.strptime(tdt_str, '%y%m%d%H%M%S')
        # print('tdt: ', tdt)
        # maxtc = int.from_bytes(body[12:14], 'big')
        # print('maxtc: ', maxtc / 10)
        # gr = int.from_bytes(body[14:16], 'big')
        # lc = int.from_bytes(body[16:18], 'big')
        # lv = int.from_bytes(body[18:20], 'big')
        # temp = int.from_bytes(body[20:22], 'big')
        # humi = int.from_bytes(body[22:23], 'big')
        # ev = int.from_bytes(body[23:25], 'big')
        # print('gr: ', gr / 1000)
        # print('lc: ', lc / 100)
        # print('lv: ', lv / 100)
        # print('temp: ', temp / 10)
        # print('humi: ', humi, '%')
        # print('ev: ', ev / 10)
        # data = [
        #     {
        #         'measurement': 'test_tab',
        #         'time': datetime.datetime.utcfromtimestamp(tdt.timestamp()).isoformat(),
        #         'tags': {
        #             'gateway_id': gateway_id,
        #             'node_id': node_id
        #         },
        #         'fields': {
        #             'maxtc': maxtc,
        #             'gr': gr,
        #             'lc': lc,
        #             'lv': lv,
        #             'temp': temp,
        #             'humi': humi,
        #             'ev': ev
        #         }
        #     }
        # ]
        # if self.need_save:
        #     self.influxdb.saveall(data=data)
        # values = {'maxtc': maxtc,
        #           'gr': gr,
        #           'lc': lc,
        #           'lv': lv,
        #           'temp': temp,
        #           'humi': humi,
        #           'ev': ev}
        # if operator.ne(values, self.data_last):  # change the redis while the values is different
        #     self.data_last = values
        #     rsl = self.redis.get_conn().hmset(str(gateway_id) + str(node_id), values)
        #     if not rsl:
        #         print('ERROR! Fail to refresh redis.')

    def start(self):
        try:
            print('start consuming......')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.close()


if __name__ == '__main__':
    handler1 = RawDataHandler(need_save=True)
    handler1.start()
