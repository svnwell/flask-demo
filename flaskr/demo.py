# -*- coding: utf-8 -*-
""" Demo interfaces to show how to use this
    demo framework. """

from flask import(
    current_app, Blueprint
)
from .util import *
from . import(
    DBA
)

bp = Blueprint('demo', __name__, url_prefix='/api/demo')

class Demo:
    def __init__(self):
        self.db = DBA('demo')

    def uploads(self, params):
        current_app.logger.info("name:%s", params['name'])
        current_app.logger.info("file name:%s", params['fname'])

        url = better_path(current_app.config['PIC_URL'])+params['fname']

        return on_success(url)

    def search(self, params):
        select = Demo._select(params)
        rows, count = self.db.paging_find(select, nfields=['_id'],
                                          pgidx=params['pageIndex'],
                                          pgsz=params['pageSize'])

        return on_success(rows, count)

    def add(self, params):
        self.db.insert_one(params)

        return on_success()

    @staticmethod
    def _select(params):
        select = {}
        return select


d = Demo()

# @upload auto storage file 'demo.jpg' to current_app.config['STATIC_PATH]
@bp.route('/uploads', methods=('POST', 'OPTIONS'))
@upload('STATIC_PATH', uname='demo', appfix='.jpg')
def uploads(params):
    return d.uploads(params)

# 如果请求参数中没有pageIndex 和 pageSize， 那么bind
# 会自动在请求参数中添加 pageIndex 和 pageSize
@bp.route('/search', methods=('GET', 'POST', 'OPTIONS'))
@bind({'pageIndex': 1, 'pageSize':20})
def search(params):
    return d.search(params)


# name 必填， text 默认 this is a demo
# index 必填,必须大于等于1
@bp.route('/add', methods=('GET', 'POST', 'OPTIONS'))
@bind({'name': 'str',
       'text': 'str,$default:"this is a demo."',
       'index': 'int,$default:required,$gte:1'})
def add(params):
    return d.add(params)
