#!/usr/bin/env python

import os
from flaskr import create_app

os.environ['FLASK_ENV'] = 'development'

app = create_app()

