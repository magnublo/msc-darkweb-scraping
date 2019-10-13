from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

from definitions import DB_ENGINE_URL, DB_CLIENT_ENCODING
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
        return existing_settings
    else:
        settings = Settings(refill_queue_when_complete=True)
        db_session.add(settings)
        db_session.commit()
        return settings


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

def get_error_string(scraping_object, error_traceback, local_variables):
    object_variables = vars(scraping_object)
    local_variable_strings = [str(key) + ": " + str(local_variables[key]) for key in local_variables.keys()]
    object_variable_strings = [str(key) + ": " + str(object_variables[key]) for key in object_variables.keys()]
    return "\n\n\n".join([error_traceback] + local_variable_strings + object_variable_strings)