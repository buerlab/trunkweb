__author__ = 'zhongqiling'

import tornado
from tornado.gen import coroutine
from functools import wraps
from datetime import datetime, time
from tornado.options import options
from tornado.gen import Return
from mylog import mylog, getLogText
from dbmodels import *

def sync_loop_call(delta=60 * 1000):
    """
    Wait for func down then process add_timeout
    """
    def wrap_loop(func):
        @wraps(func)
        @coroutine
        def wrap_func(*args, **kwargs):
            options.logger.info("function %r start at %d" % (func.__name__, int(time.time())))
            try:
                yield func(*args, **kwargs)
            except Exception, e:
                options.logger.error("function %r error: %s" % (func.__name__, e))
            options.logger.info("function %r end at %d" % (func.__name__, int(time.time())))
            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(milliseconds=delta), wrap_func)

        return wrap_func

    return wrap_loop

