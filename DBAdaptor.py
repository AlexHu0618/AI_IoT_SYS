# -*- coding: utf-8 -*-
# @Time    : 12/17/19 2:44 AM
# @Author  : Alex Hu
# @Contact : jthu4alex@163.com
# @FileName: DBAdaptor.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0

from config import config_parser as cper
from influxdb import InfluxDBClient
from redis import ConnectionPool, Redis


class DBAdaptor(object):
    def __init__(self, db_type='influxdb'):
        if db_type == 'redis':
            self.conn = self.__init_redis()
        elif db_type == 'influxdb':
            self.conn = self.__init_influxdb()
        else:
            print('Error! Please specify the type of database.')

    def __init_influxdb(self):
        conf = cper.read_yaml_file('influxdb')
        host = conf['host']
        port = conf['port']
        username = conf['username']
        pwd = conf['password']
        database = conf['database']
        use_udp = conf['use_udp']
        udp_port = conf['udp_port']
        client = InfluxDBClient(host=host, port=port, username=username, password=pwd, database=database)
        if client is None:
            print('ERROR! No DB connection was built!')
        return client

    def __init_redis(self):
        conf = cper.read_yaml_file('redis')
        host = conf['host']
        port = conf['port']
        max_conn = conf['max_conn']
        POOL = ConnectionPool(host=host, port=port, max_connections=max_conn)
        client = Redis(connection_pool=POOL)
        if client is None:
            print('ERROR! No DB connection was built!')
        return client

    def saveall(self, data):
        rsl = self.conn.write_points(data)
        if not rsl:
            print('Fail to saveall!')

    def createtab(self):
        pass

    def get_conn(self):
        return self.conn


db = DBAdaptor()
