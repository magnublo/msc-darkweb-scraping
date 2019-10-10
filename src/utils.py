from sqlalchemy.orm.session import Session as SQLAlchemySession

from src.models.settings import Settings


def pretty_print_GET(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """
    return '{}\n{}\r\n{}\r\n\r'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items())
    )

def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """
    return '{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    )

def get_settings(db_session : SQLAlchemySession):
    existing_settings = db_session.query(Settings).first()
    if existing_settings:
        return existing_settings
    else:
        settings = Settings(refill_queue_when_complete=True)
        db_session.add(settings)
        db_session.commit()
        return settings

import types
from pprint import pformat
from threading import RLock

class SynchronizeMethodWrapper:
    """
    Wrapper object for a method to be called.
    """
    def __init__( self, obj, func, name, rlock ):
        self.obj, self.func, self.name = obj, func, name
        self.rlock = rlock
        assert obj is not None
        assert func is not None
        assert name is not None

    def __call__( self, *args, **kwds ):
        """
        This method gets called before a method is called to sync access to the core object.
        """
        with self.rlock:
            rval = self.func(*args, **kwds)
            return rval


class SynchronizeProxy(object):
    """
    Proxy object that synchronizes access to a core object methods and attributes that don't start with _.
    """
    def __init__( self, core ):
        self._obj = core
        self.rlock = RLock()

    def __getattribute__( self, name ):
        """
        Return a proxy wrapper object if this is a method call.
        """
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        else:
            att = getattr(self._obj, name)
            if type(att) is types.MethodType:
                return SynchronizeMethodWrapper(self, att, name, object.__getattribute__(self, "rlock"))
            else:
                return att

    def __setitem__( self, key, value ):
        """
        Delegate [] syntax.
        """
        name = '__setitem__'
        with self.rlock:
            att = getattr(self._obj, name)
            pmeth = SynchronizeMethodWrapper(self, att, name, self.rlock)
            pmeth(key, value)


def error_is_sqlalchemy_error(error_string):
    return error_string.find("site-packages/sqlalchemy") != -1 \
            or error_string.find("\'NoneType\' object has no attribute \'have_result_set\'") != -1 \
            or error_string.find("MySQL") != -1


def print_error_to_file(thread_id, error_string):
    file_name = "thread_" + str(thread_id) + "_error"
    file = open(file_name, "w")
    file.write(error_string)
    file.close()