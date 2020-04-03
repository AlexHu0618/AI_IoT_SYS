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
        conf = cper.read_yaml_file('redis')
        host = conf['host']
        port = conf['port']
        db = conf['db']
        max_conn = conf['max_conn']
        self.redis_pool = ConnectionPool(host=host, port=port, max_connections=max_conn, db=db)

    def create_conn(self, db_type='influxdb'):
        if db_type == 'redis':
            return RedisDB(self.redis_pool)
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

    def __del__(self):
        self.redis_pool.disconnect()


class InfluxDB(DBAdaptor):
    def __init__(self):
        conf = cper.read_yaml_file('influxdb')
        host = conf['host']
        port = conf['port']
        username = conf['username']
        pwd = conf['password']
        self.database = conf['database']
        use_udp = conf['use_udp']
        udp_port = conf['udp_port']
        self.client = InfluxDBClient(host=host, port=port, username=username, password=pwd, database=self.database)
        if self.client is None:
            print('ERROR! No InfluxDB connection was built!')
        else:
            self.__setting()

    def saveall(self, data):
        rsl = self.client.write_points(data)
        if not rsl:
            print('Fail to saveall!')

    def exec_sql(self, sql):
        rsl = self.client.query(sql)
        points = rsl.get_points()
        return points

    def __setting(self):
        """
        1\ create database if not existed
        2\ create rp if not existed
        :return:
        """
        rsl = self.client.get_list_database()
        if {'name': self.database} not in rsl:
            self.client.create_database(dbname=self.database)
        rsl = self.client.get_list_retention_policies(database=self.database)
        is_rp_7d_existed = False
        is_rp_30d_existed = False
        for i in rsl:
            if i['name'] == 'rp_7d':
                is_rp_7d_existed = True
            elif i['name'] == 'rp_30d':
                is_rp_30d_existed = True
            else:
                continue
        if not is_rp_7d_existed:
            self.client.create_retention_policy(name='rp_7d', duration='168h', replication='1', database=self.database,
                                                default=True, shard_duration='24h')
        if not is_rp_30d_existed:
            self.client.create_retention_policy(name='rp_30d', duration='720h', replication='1', database=self.database,
                                                default=False, shard_duration='24h')

    def __del__(self):
        pass


class RedisDB(DBAdaptor):
    def __init__(self, pool):
        self.client = Redis(connection_pool=pool)
        if self.client is None:
            print("Fail to build redis client")

    def get_conn(self):
        if self.client is not None:
            return self.client
        else:
            print("Fail because there is no redis conn")
            return None

    def __del__(self):
        pass


class MysqlDB(DBAdaptor):
    def __init__(self):
        conf = cper.read_yaml_file('mysql')
        host = conf['host']
        user = conf['user']
        pwd = conf['password']
        db = conf['database']
        charset = conf['charset']
        self.conn = pymysql.connect(host=host, user=user, password=pwd, database=db, charset=charset)
        self.cursor = self.conn.cursor()

    def get_data(self, sql):
        self.cursor.execute(sql)
        rsl = self.cursor.fetchall()
        return rsl

    def close(self):
        self.cursor.close()
        self.conn.close()

    def __del__(self):
        self.cursor.close()
        self.conn.close()


db_factory = DBAdaptor()
