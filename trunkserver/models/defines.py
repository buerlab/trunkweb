__author__ = 'zhongqiling'

from tornado.gen import  coroutine, Return
from functools import wraps
from models.base import ValidationError, InvalidDocumentError
from pymongo.errors import AutoReconnect
import sys


def coroutineDebug(func):
    @wraps(func)
    @coroutine
    def debuger(*args, **kwargs):
        try:
            resp = yield func(*args, **kwargs)
            raise Return(resp)
        except (AttributeError, IOError, IndexError, KeyError, NameError, SyntaxError, TypeError, \
                ValidationError, InvalidDocumentError, UnboundLocalError, AutoReconnect) as e:
            exc_type, exc_value, traceback = sys.exc_info()
            sys.excepthook(exc_type, exc_value, traceback)
        # except Exception:
        #     exc_type, exc_value, traceback = sys.exc_info()
        #     sys.excepthook(exc_type, exc_value, traceback)
    return debuger
