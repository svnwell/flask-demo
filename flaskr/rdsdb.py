# -*- coding: utf-8 -*-
import redis
import hashlib

class RediPool(object):
    _pools = {}

    def __init__(self, app):
        conn = app.config['DEFAULT_REDIS_CONN']
        pool = redis.ConnectionPool(host=conn['host'], port=conn['port'],
                                    password=conn['password'], db=conn['db'])

        self.key = self.gen_key(conn)
        RediPool._pools[self.key] = pool


    def redis(self, conn=None):
        if not conn:
            return redis.Redis(connection_pool=RediPool._pools[self.key])

        k = self.gen_key(conn)
        if RediPool._pools.get(k):
            return redis.Redis(connection_pool=RediPool._pools[k])

        pool = redis.ConnectionPool(host=conn['host'], port=conn['port'],
                                    password=conn['password'], db=conn['db'])
        RediPool._pools[k] = pool

        return redis.Redis(connection_pool=pool)


    def gen_key(self, conn=None):
        if not conn:
            return self.key

        m = hashlib.md5()
        m.update(conn['host']+str(conn['port'])+conn['password']+str(conn['db']))

        return m.hexdigest()
