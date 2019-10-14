import inspect
import time
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

from definitions import DB_ENGINE_URL, DB_CLIENT_ENCODING, MYSQL_TEXT_COLUMN_MAX_LENGTH, \
    MYSQL_MEDIUM_TEXT_COLUMN_MAX_LENGTH
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

def get_settings():
    engine = get_engine()
    db_session = get_db_session(engine)
    existing_settings = db_session.query(Settings).first()
    if existing_settings:
        res = existing_settings
    else:
        settings = Settings(refill_queue_when_complete=True)
        db_session.add(settings)
        db_session.commit()
        res = settings

    db_session.expunge_all()
    db_session.close()
    db_session.close()
    return res


def error_is_sqlalchemy_error(error_string):
    return error_string.find("site-packages/sqlalchemy") != -1 \
            or error_string.find("\'NoneType\' object has no attribute \'have_result_set\'") != -1 \
            or error_string.find("MySQL") != -1


def print_error_to_file(thread_id, error_string):
    file_name = "thread_" + str(thread_id) + "_error"
    file = open(file_name, "w")
    file.write(error_string)
    file.close()


def get_engine():
    engine = create_engine(DB_ENGINE_URL, encoding=DB_CLIENT_ENCODING, echo=False, connect_args={'buffered': True})
    return engine

def get_db_session(engine):
    Session = sessionmaker(
        bind=engine)
    db_session = Session()
    db_session.rollback()
    return db_session

def get_error_string(scraping_object, error_traceback, sys_exec_info):
    time_of_error = str(datetime.fromtimestamp(time.time()))
    tb_last = sys_exec_info[2]
    func_name = str(inspect.getinnerframes(tb_last)[0][3])
    local_variable_strings = ["["+func_name+"()]" + str(key) + ": " + str(tb_last.tb_frame.f_locals[key]) for key in
                              tb_last.tb_frame.f_locals.keys()]
    while tb_last.tb_next:
        tb_last = tb_last.tb_next
        func_name = str(inspect.getinnerframes(tb_last)[0][3])
        local_variable_strings = local_variable_strings + ["["+func_name+"()]" + str(key) + ": " + str(tb_last.tb_frame.f_locals[key])
                                                           for key in
                                                           tb_last.tb_frame.f_locals.keys()]

    object_variables = vars(scraping_object)
    object_variable_strings = [str(key) + ": " + str(object_variables[key]) for key in object_variables.keys()]
    return "\n\n\n".join([time_of_error] + [error_traceback] + local_variable_strings + object_variable_strings)

def kill_all_existing_db_connections_for_user(db_username):
    stmt = "SELECT id, time FROM information_schema.processlist WHERE user='"+db_username+"' ORDER BY time ASC"

    engine = get_engine()

    with engine.connect() as con:
        rs = con.execute(stmt)

        rows = [row for row in rs]

        for row in rows[1:]:
            kill_statement = "KILL " + str(row[0]) + ";"
            con.execute(kill_statement)

def shorten_text(max_length, text):
    if len(text.encode("utf8")) <= max_length:
        return text.strip()

    mxlen = max_length

    while (text.encode("utf8")[mxlen - 1] & 0xc0 == 0xc0):
        mxlen -= 1

    return text.encode("utf8")[0:mxlen].decode("utf8").strip()


def _shorten_for_text_column(text):
    return shorten_text(MYSQL_TEXT_COLUMN_MAX_LENGTH, text)


def _shorten_for_medium_text_column(text):
    return shorten_text(MYSQL_MEDIUM_TEXT_COLUMN_MAX_LENGTH, text)