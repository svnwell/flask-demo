# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
from flaskr import create_app

os.environ['FLASK_ENV'] = 'development'

app = create_app()

app.run(host='0.0.0.0', port=5000)
