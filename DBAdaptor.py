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
import pymysql


class DBAdaptor(object):
    def __init__(self):
        pass

    def create_conn(self, db_type='influxdb'):
        if db_type == 'redis':
            return Redis()
        elif db_type == 'influxdb':
            return InfluxDB()
        elif db_type == 'mysql':
            return Mysql()
        else:
            print('Error! Please specify the type of database.')
            return None

    def saveall(self, data):
        rsl = self.conn.write_points(data)
        if not rsl:
            print('Fail to saveall!')

    def createtab(self):
        pass

    def get_conn(self):
        return self.conn

    def get_data(self):
        print('factory')


class InfluxDB(DBAdaptor):
    def __init__(self):
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


class Redis(DBAdaptor):
    def __init__(self):
        conf = cper.read_yaml_file('redis')
        host = conf['host']
        port = conf['port']
        max_conn = conf['max_conn']
        POOL = ConnectionPool(host=host, port=port, max_connections=max_conn)
        client = Redis(connection_pool=POOL)
        if client is None:
            print('ERROR! No DB connection was built!')


class Mysql(DBAdaptor):
    def __init__(self):
        conf = cper.read_yaml_file('mysql')
        host = conf['host']
        user = conf['user']
        pwd = conf['password']
        charset = conf['charset']
        conn = pymysql.connect(host=host, user=user, password=pwd, charset=charset)
        self.cursor = conn.cursor()

    def get_data(self, sql):
        rsl = self.cursor.execute(sql)
        rsl = self.cursor.fetchall()
        return rsl
