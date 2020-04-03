# -*- coding: utf-8 -*-
# @Time    : 12/5/19 5:01 PM
# @Author  : Alex Hu
# @Contact : jthu4alex@163.com
# @FileName: RawDataHandler.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0

import pika
from config import config_parser as cper
from DBAdaptor import db_factory
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
        """
        1\ get hash from redis by gateway_id;
        2\
        :param ch:
        :param method:
        :param properties:
        :param body:
        :return:
        """
        data = pickle.loads(body)
        print('got data: ', data)
        gateway_id = data['gateway_id']
        if self.redis.exists(gateway_id):
            rsl = self.redis.hgetall(gateway_id)
            value = {k.decode(): v.decode() for k, v in rsl.items()}
            df_struct = list(map(int, value['df_struct'].split(',')))
            id_size = tuple(eval(value['id_size']))
            table_name = value['table_name']
            rawdata = data['data_frame']
            map(float, rawdata)
            print(rawdata)
            min_num = min(len(df_struct), len(rawdata))
            points = []
            for index in range(min_num):
                point = {
                    'measurement': table_name,
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

    def start(self):
        try:
            print('start consuming......')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.close()


if __name__ == '__main__':
    handler1 = RawDataHandler(need_save=True)
    handler1.start()
