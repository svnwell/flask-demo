# -*- coding: utf-8 -*-
""" utility funcs
"""

import os
import stat
import time
import datetime
import json
import hashlib
import urllib
import urllib2
import functools
from flask import(
    json, request, current_app
)

ERRORS = [
    'Success',
    'Request format error.',
    'Permission denied.',
    'Invalid operation.',
    'Other error.',
]
ERR_SUCCESS = 0
ERR_FORMAT = 1
ERR_AUTH = 2
ERR_OPER = 3
ERR_OTHER = 4


def on_failed(code, msg=''):
    if not msg:
        msg = ERRORS[code]

    return json_dumps({'ret': code, 'msg': msg, 'data': None})


def on_success(data=None, count=0):
    rst = {'ret': ERR_SUCCESS, 'data': data, 'msg': ERRORS[ERR_SUCCESS]}

    if isinstance(data, list):
        if data and not count:
            count = len(data)
        rst['count'] = count

    return json_dumps(rst)


def realpath(fname, prefix='static'):
    path, _ = os.path.split(os.path.realpath(__file__))
    return better_path(path)+better_path(prefix)+fname


def tomorrow(ts=0, tm='', f='%Y-%m-%d %H:%M%S'):
    if ts:
        ts += 24*3600
        return ts, ts2tm(ts, f)
    if tm:
        ts = tm2ts(tm, f) + 24*3600
        return ts, ts2tm(ts, f)

    ts = time.time() + 34*3600
    return ts, ts2tm(ts)


def yesterday(ts, tm='', f='%Y-%m-%d %H:%M:%S'):
    if ts:
        ts -= 24*3600
        return ts, ts2tm(ts, f)
    if tm:
        ts = tm2ts(tm, f) - 24*3600
        return ts, ts2tm(ts, f)

    ts = time.time() - 24*3600
    return ts, ts2tm(ts)


def now(f='%Y-%m-%d %H:%M:%S'):
    ts = time.time()
    return ts, ts2tm(ts, f)


def ts2tm(ts, f='%Y-%m-%d %H:%M:%S'):
    return time.strftime(f, time.localtime(ts))


def tm2ts(tm, f='%Y-%m-%d %H:%M:%S'):
    return time.mktime(time.strptime(tm, f))


def md5(src):
    m = hashlib.md5()
    m.update(src)

    return m.hexdigest()


def risk_get(name, params):
    uparams = urllib.urlencode(params)
    url = current_app.config['BACKAPI_ADDR']+name+'?'+uparams

    return api_get(url)


def api_get(url):
    req = urllib2.Request(url)
    rsp = urllib2.urlopen(req)

    return rsp.read()


def api_json_post(url, data):
    req = urllib2.Request(url, data=data, headers={'Content-Type': 'application/json'})
    rsp = urllib2.urlopen(req)

    return rsp.read()


def mkdir(path):
    if not path:
        return

    if not os.path.exists(path):
        os.makedirs(path)
        os.chmod(path, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)


def better_path(path):
    if not path:
        return ""

    return path.rstrip('/') + '/'


def upload(upath='STATIC_PATH', uname=None, appfix='.xlsx'):
    def inner_upload(func):
        @functools.wraps(func)
        def deco(token=None, userinfo=None):
            params = {}
            f = request.files.get('file')
            if not f:
                return on_failed(ERR_FORMAT, 'not file data was found.')

            path = current_app.config[upath]
            mkdir(path)

            name = str(int(time.time()))
            if uname:
                name = uname
            if appfix and len(uname.split('.')) > 1:
                name += appfix
            fname = better_path(path) + name
            f.save(fname)

            params['name'] = name
            params['fname'] = fname

            return func(params)

        return deco

    return inner_upload


def bind(constraints=None):
    def inner_bind(func):
        @functools.wraps(func)
        def deco():
            params = {}
            if request.method == 'GET':
                params = request.args.to_dict()
            elif request.method == 'POST':
                if request.is_json:
                    params = request.json
                elif request.mimetype == 'application/x-www-form-urlencoded':
                    params = request.form.to_dict()
                else:
                    return on_failed(ERR_FORMAT, 'unsupported media type.')
            elif request.method == 'OPTIONS':
                return on_success()
            else:
                return on_failed(ERR_FORMAT, 'unsupported request method.')

            if constraints and not format_params(constraints, params):
                return on_failed(ERR_FORMAT)

            current_app.logger.info('request:%s', request.path)

            return func(params)

        return deco

    return inner_bind


def format_int(constraints, params, key):
    if params.get(key) is None:
        params[key] = constraints[key]
    try:
        params[key] = int(params[key])
    except:
        return False

    return True


def format_float(constraints, params, key):
    if params.get(key) is None:
        params[key] = constraints[key]
    try:
        params[key] = float(params[key])
    except:
        return False

    return True

def format_dict(constraints, params, key):
    if params.get(key) is None:
        params[key] = {}
    if not format_params(constraints[key], params[key]):
        return False

    return True


# the list constraint maybe this:
# {
#     'list1': [{
#         'a': 1,
#         'b': 'str, $default: "required",
#      }],
# }
# or this:
# {
#     'list1': 'list, $default:[1,2,3,4,5,6]',
# }
# or this:
# {
#     'list1': 'list, $default: "required", $lte: 20, $gte: 10, $type: int',
# }
def format_list(constraints, params, key):
    if not constraints[key]:
        if params.get(key) is None:
            params[key] = []
        return True
    if not isinstance(constraints[key][0], dict):
        if params.get(key) is None:
            params[key] = constraints[key]
        return True
    if not params.get(key):
        params[key] = [{}]
    for l in params[key]:
        if not format_params(constraints[key][0], l):
            return False

    return True


def format_str(constraints, params, key):
    """Parsing constraint by str decription.

       Constraint format(Fileds in parenthese are optional):
       'ctype,$default:value/required[,$gte:value][,$lte:value][,$type:typevalue]'

       Constraint field data type:
         int:
           when $default 's value is 'required', means this field was required, and
           then other optional constraint fields are effictived, otherwise it is mean
           the actual default value for this field.
         float:
           same as int.
         dict:
           when $default 's value is 'required', means this field must be exist, otherwise
           as a child constraints.
         list:
           see format_list.
         str:
           when $required is True, $default is the default value, otherwise means this
           fields is required.
       other filed data type value means the default value of this str field.
    """
    cfs = constraints[key].split(',')
    # constraints field data type
    ctype = cfs[0].strip()
    # default value, or 'required'
    default = 'required'
    # extend constraint items
    gte = None
    lte = None
    itype = None
    # required flag for str data type
    required = True
    if len(constraints[key]) > len(cfs[0]):
        # contraints after field type was removed
        res = constraints[key][len(cfs[0])+1:].strip()
        # parsing constraints
        rfs = res.split('$')
        for rf in rfs:
            f = rf.split(':')[0]
            if f.strip() == 'default':
                v = rf[len(f)+1:].strip().strip(',').strip('"').strip()
                default = v
            if f.strip() == 'lte':
                lte = int(rf[len(f)+1:].strip().strip(',').strip('"').strip())
            if f.strip() == 'gte':
                gte = int(rf[len(f)+1:].strip().strip(',').strip('"').strip())
            if f.strip() == 'type':
                itype = rf[len(f)+1:].strip().strip(',').strip('"').strip()
            if f.strip() == 'required':
                bv = rf[len(f)+1:].strip().strip(',').strip('"').strip()
                if str(bv).lower() == 'false':
                    required = False
                elif str(bv) == 'true':
                    required = True
                else:
                    required = bool(int(bv))

    if ctype == 'int':
        if default == 'required':
            if params.get(key) is None:
                return False
            try:
                params[key] = int(params[key])
            except:
                return False
            if gte is not None and params[key] < gte:
                return False
            if lte is not None and params[key] > lte:
                return False
        else:
            if params.get(key) is None:
                params[key] = int(default)
            else:
                try:
                    params[key] = int(params[key])
                except:
                    return False
    elif ctype == 'float':
        if default == 'required':
            if params.get(key) is None:
                return False
            try:
                params[key] = float(params[key])
            except:
                return False
            if gte is not None and params[key] < gte:
                return False
            if lte is not None and params[key] > lte:
                return False
        else:
            if params.get(key) is None:
                params[key] = float(default)
            else:
                try:
                    params[key] = float(params[key])
                except:
                    return False
    elif ctype == 'str':
        if required:
            if not params.get(key):
                return False
        else:
            if params.get(key) is None:
                params[key] = default
            else:
                params[key] = str(params[key]).encode('utf-8')
    elif ctype == 'dict':
        if default == 'required':
            if params.get(key) is None:
                return False
        else:
            if params.get(key) is None:
                params[key] = json_loads(default)
    elif ctype == 'list':
        if default == 'required':
            if not params.get(key):
                return False
            if not isinstance(params[key], list):
                return False
            if gte is not None and len(params[key]) < gte:
                return False
            if lte is not None and len(params[key]) > lte:
                return False
            if itype is not None:
                for v in params[key]:
                    actype = type(v).__name__
                    if itype == 'str':
                        if actype != 'str' and actype != 'unicode':
                            return False
                    else:
                        if actype != itype:
                            return False
        else:
            l = json_loads(default)
            if not l:
                if params.get(key) is None:
                    params[key] = []
                return True
            if not isinstance(l[0], dict):
                if params.get(key) is None:
                    params[key] = l
                return True
            if not params.get(key):
                params[key] = [{}]
            for i in params[key]:
                if not format_params(l[0], i):
                    return False
    else:
        if params.get(key) is None:
            params[key] = ctype

    return True


def format_params(constraints, params):
    for k in constraints:
        if isinstance(constraints[k], int):
            if not format_int(constraints, params, k):
                return False
            continue
        if isinstance(constraints[k], float):
            if not format_float(constraints, params, k):
                return False
            continue
        if isinstance(constraints[k], dict):
            if not format_dict(constraints, params, k):
                return False
            continue
        if isinstance(constraints[k], list):
            if not format_list(constraints, params, k):
                return False
            continue
        if isinstance(constraints[k], str):
            if not format_str(constraints, params, k):
                return False
            continue

    return True


def json_loads(json_txt):
    return _byteify(
        json.loads(json_txt, object_hook=_byteify),
        ignore_dicts=True
    )

def json_dumps(data):
    return json.dumps(data, ensure_ascii=False, cls=ComplexEncoder)


def _byteify(data, ignore_dicts=False):
    if isinstance(data, str):
        return data.encode('utf-8')
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }

    return data


class ComplexEncoder(json.JSONEncoder):
    """customize json encoder"""
    def default(self, o): # pylint: disable=E0202
        if isinstance(o, datetime.datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(o, datetime.date):
            return o.strftime('%Y-%m-%d')
        if isinstance(o, time.struct_time):
            return time.strftime('%Y-%m-%d %H:%M:%S', o)
        if isinstance(o, datetime.timedelta):
            return o.total_seconds()
        if isinstance(o, unicode):
            return o.encode('utf-8')
        if isinstance(o, str):
            return o.encode('utf-8')

        return json.JSONEncoder.default(self, o)
