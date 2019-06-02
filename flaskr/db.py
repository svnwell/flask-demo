# -*- coding: utf-8 -*-

"""Mongo operation interfaces.
"""

import pymongo
from pymongo import MongoClient

class DBAdaptor(object):
    """Mongo operation interfaces."""

    _conn = None

    def __init__(self, app, db=None, col=None):
        self._app = app

        DBAdaptor._conn = MongoClient(app.config['MONGO_CONN'], connect=False)
        self._db = DBAdaptor._conn[app.config['MONGO_DEFAULT_DATABASE']]
        if db:
            self._db = DBAdaptor._conn[db]

        self._col = None
        if col:
            self._col = self._db[col]

    def __call__(self, collection, database=None):
        return DBAdaptor(self._app, db=database, col=collection)

    def find_one(self, selects, nfields=None, sorts=None, collection=None):
        """Find rows from mongo.
        Retrieves rows from mongo with the given filters and orders

        Args:
            selects: collection filters with bson/json formats.
            nfields: fields need to be ignored.
            sorts: fields to specify the sorted order, '-' header
               means descending order.
        Returns:
            List of rows
        """
        col = self._col
        if collection:
            col = self._db[collection]

        orders = None
        if sorts:
            orders = []
            for s in sorts:
                if s[0] == '-':
                    orders.append((s[1:], pymongo.DESCENDING))
                    continue
                orders.append((s.lstrip('+'), pymongo.ASCENDING))

        projections = None
        if nfields:
            projections = {}
            for nfd in nfields:
                projections[nfd] = False

        data = col.find_one(
            filter=selects, sort=orders,
            projection=projections)

        return data
    
    def find(self, selects, nfields=None, sorts=None, collection=None):
        """Find rows from mongo.
        Retrieves rows from mongo with the given filters and orders

        Args:
            selects: collection filters with bson/json formats.
            nfields: fields need to be ignored.
            sorts: fields to specify the sorted order, '-' header
               means descending order.
        Returns:
            List of rows
        """
        col = self._col
        if collection:
            col = self._db[collection]

        orders = None
        if sorts:
            orders = []
            for s in sorts:
                if s[0] == '-':
                    orders.append((s[1:], pymongo.DESCENDING))
                    continue
                orders.append((s.lstrip('+'), pymongo.ASCENDING))

        projections = None
        if nfields:
            projections = {}
            for nfd in nfields:
                projections[nfd] = False

        data = col.find(
            filter=selects, sort=orders,
            projection=projections)

        return list(data)

    def paging_find(self, selects=None, nfields=None, sorts=None, collection=None,
                    pgidx=0, pgsz=0):
        """Paging find rows from mongo
        Retrieves rows from mongo with given filters and orders,
        and then paging the results.

        Args:
            selects: collection filters with bson/json formats.
            nfields: fields need to be ignored.
            sorts: fileds to specify the sorted order, '-' header
                means descending order.
            pgidx: paging index starting with number 1.
            pgsz: paging size.
        Returns:
            paged rows.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        orders = None
        if sorts:
            orders = []
            for s in sorts:
                if s[0] == '-' and len(s) > 1:
                    orders.append((s[1:], pymongo.DESCENDING))
                    continue
                o = s.lstrip('+')
                if len(o) > 0:
                    orders.append((o, pymongo.ASCENDING))

        projections = None
        if nfields:
            projections = {}
            for nfd in nfields:
                projections[nfd] = False

        data = col.find(
            filter=selects, sort=orders,
            projection=projections)
        count = data.count()

        return list(data.skip((pgidx-1)*pgsz).limit(pgsz)), count

    def insert_one(self, data, collection=None):
        """Insert one row to mongo.
           Args:
               data: the row to be inserted.
           Returns:
               inserted _id.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.insert_one(data).inserted_id

    def insert_many(self, data, collection=None):
        """Insert many rows to mongo.
        Args:
            data: iterable of documents to be inserted.
        Returns:
            list of _id of the inserted documents.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.insert_many(data).inserted_ids

    def update_one(self, selects, updata, collection=None):
        """Update one row in mongo.
           Args:
               selects: a query that matches the document to update.
               updata: the modifications to be update.
           Returns:
               update result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.update_one(selects, updata, upsert=False)

    def upset_one(self, selects, updata, collection=None):
        """Update one row in mongo, just for $set operation.
           Args:
               selects: a query that matches the document to update.
               updata: the modifications to be update.
           Returns:
               update result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.update_one(selects, {'$set': updata}, upsert=False)

    def update_many(self, selects, updata, collection=None):
        """Update many rows in mongo.
           Args:
               selects: a query that matches the documents to update.
               updata: the modifications to be update.
           Returns:
               update result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.update_many(selects, updata, upsert=False)

    def upset_many(self, selects, updata, collection=None):
        """Update many rows in mongo, just for $set operation
           Args:
               selects: a query that matches the documents to update.
               updata: the modifications to be update.
           Returns:
               update result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.update_many(selects, {'$set': updata}, upsert=False)

    def upsert_one(self, selects, updata, collection=None):
        """Update/insert one row to mongo, just for $set operation
           Args:
               selects: a query that matches the documents to update.
               updata: the modifications to be update.
           Returns:
               update result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        print 'upsert col:', col.name
        return col.update_one(selects, {'$set': updata}, upsert=True)

    def upsert_many(self, selects, updata, collection=None):
        """Update/insert many rows to mongo, just for $set operation
           Args:
               selects: a query that matches the documents to update.
               updata: the modifications to be update.
           Returns:
               update result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.update_many(selects, {'$set': updata}, upsert=True)

    def delete_one(self, selects, collection=None):
        """Delete one row from mongo.
           Args:
              selects: a query that matches the documents to delete.
           Returns:
              mongo delte_one result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.delete_one(selects)

    def delete_many(self, selects, collection=None):
        """Delete one row from mongo.
           Args:
              selects: a query that matches the documents to delete.
           Returns:
              mongo delte_one result.
        """
        col = self._col
        if collection:
            col = self._db[collection]

        return col.delete_many(selects)

    def incsert(self, data, *keys):
        n = self._col.count_documents({})
        data['_id'] = n
        for k in keys:
            data[k] = n

        return self._col.insert_one(data)

    def aggregate(self, pipeline, collection=None):
        col = self._col
        if collection:
            col = self._db[collection]

        return list(col.aggregate(pipeline))

    @staticmethod
    def get_conn():
        return DBAdaptor._conn
