# -*- coding: utf-8 -*-
""" Init salesman instance
"""

from flask_cors import CORS
from flask_docs import ApiDoc
from flask import(
    Flask, jsonify
)

DBA = None
RDS = None

def create_app(test_config=None, env=None):
    """ create and config the app """
    app = Flask(__name__)
    # cors auth
    CORS(app)

    if test_config is None:
        app.config.from_object('flaskr.default_settings')
        if env:
            app.config.from_envvar(env)
    else:
        app.config.from_mapping(test_config)

    from . import db
    global DBA
    if not DBA:
        DBA = db.DBAdaptor(app)

    # from .import rdsdb
    # global RDS
    # if not RDS:
    #     RDS = rdsdb.RediPool(app)

    from . import(
        demo
    )
    app.register_blueprint(demo.bp)

    return app
