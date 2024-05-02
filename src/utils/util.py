import datetime

from sanic import response

def http_response(code, msg='', data=None, status=200, **kwargs):
    output = {'code': code, 'msg': msg, 'results': data}
    if kwargs:
        output.update(kwargs)
    return response.json(output, status=status)

def get_timestamp():
    timestamp = int(datetime.datetime.utcnow().timestamp() * 1000)
    return timestamp