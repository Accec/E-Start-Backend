import datetime


def get_timestamp():
    return int(datetime.datetime.utcnow().timestamp() * 1000)
