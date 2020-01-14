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
            return RedisDB()
        elif db_type == 'influxdb':
            return InfluxDB()
        elif db_type == 'mysql':
            return MysqlDB()
        else:
            print('Error! Please specify the type of database.')
            return None

    def saveall(self, data):
        pass

    def createtab(self):
        pass

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
        self.client = InfluxDBClient(host=host, port=port, username=username, password=pwd, database=database)
        if self.client is None:
            print('ERROR! No InfluxDB connection was built!')

    def saveall(self, data):
        rsl = self.client.write_points(data)
        if not rsl:
            print('Fail to saveall!')

    def exec_sql(self, sql):
        rsl = self.client.query(sql)
        points = rsl.get_points()
        return points


class RedisDB(DBAdaptor):
    def __init__(self):
        conf = cper.read_yaml_file('redis')
        host = conf['host']
        port = conf['port']
        max_conn = conf['max_conn']
        POOL = ConnectionPool(host=host, port=port, max_connections=max_conn)
        self.client = Redis(connection_pool=POOL)
        if self.client is None:
            print('ERROR! No RedisDB connection was built!')

    def get_conn(self):
        if self.client is not None:
            return self.client
        else:
            print("Fail because there is no redis conn")
            return None


class MysqlDB(DBAdaptor):
    def __init__(self):
        conf = cper.read_yaml_file('mysql')
        host = conf['host']
        user = conf['user']
        pwd = conf['password']
        db = conf['database']
        charset = conf['charset']
        conn = pymysql.connect(host=host, user=user, password=pwd, database=db, charset=charset)
        self.cursor = conn.cursor()

    def get_data(self, sql):
        rsl = self.cursor.execute(sql)
        rsl = self.cursor.fetchall()
        return rsl


db_factory = DBAdaptor()
