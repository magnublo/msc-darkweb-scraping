import datetime
from enum import Enum

import demoji
from sqlalchemy import func, or_, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute

from definitions import MYSQL_TEXT_COLUMN_MAX_LENGTH, MYSQL_MEDIUM_TEXT_COLUMN_MAX_LENGTH, \
    SQLALCHEMY_CREATE_ENGINE_KWARGS, MYSQL_URL_PARAMS_STRING
from environmentSettings import DB_ENGINE_BASE_URL
from src.models.feedback import Feedback
from src.models.listing_observation import ListingObservation
from src.models.scraping_session import ScrapingSession
from src.models.seller import Seller
from src.models.seller_observation import SellerObservation
from src.models.settings import Settings

DB_ENGINE_URL = DB_ENGINE_BASE_URL + MYSQL_URL_PARAMS_STRING

def kill_all_existing_db_connections_for_user(db_username):
    stmt = "SELECT id, time FROM information_schema.processlist WHERE user=\'{0}\' ORDER BY time ASC".format(
        db_username)

    engine = get_engine()

    with engine.connect() as con:
        rs = con.execute(stmt)

        rows = [row for row in rs]

        for row in rows[1:]:
            kill_statement = "KILL " + str(row[0]) + ";"
            con.execute(kill_statement)


class EXTREMAL_TIMESTAMP(Enum):
    LOWEST = 0
    HIGHEST = 1


def _get_timestamp_on_scraping_session_row(db_session: Session, session_without_time,
                                           extremal_type: EXTREMAL_TIMESTAMP):
    if extremal_type is EXTREMAL_TIMESTAMP.HIGHEST:
        sqlalchemy_min_max_func = func.max
        python_min_max_func = max
        extreme_date = datetime.datetime.fromtimestamp(0).strftime("%Y-%m-%d %H:%M:%S")  # very low date
    elif extremal_type is EXTREMAL_TIMESTAMP.LOWEST:
        sqlalchemy_min_max_func = func.min
        python_min_max_func = min
        extreme_date = max(datetime.datetime.now(), datetime.datetime.utcnow()).strftime(
            "%Y-%m-%d %H:%M:%S")  # very high date
    else:
        raise Exception

    extremal_timestamps_of_child_objects = []

    extremal_timestamps_of_child_objects.append(db_session.query(sqlalchemy_min_max_func(
        func.coalesce(SellerObservation.created_date, extreme_date))).filter(
        SellerObservation.session_id == session_without_time.id).scalar())

    extremal_timestamps_of_child_objects.append(db_session.query(sqlalchemy_min_max_func(
        func.coalesce(ListingObservation.created_date, extreme_date))).filter(
        ListingObservation.session_id == session_without_time.id).scalar())

    extremal_timestamps_of_child_objects.append(db_session.query(sqlalchemy_min_max_func(
        func.coalesce(Feedback.created_date, extreme_date))).filter(
        Feedback.session_id == session_without_time.id).scalar())

    valid_extremal_timestamps_of_child_objects = [timestamp for timestamp in extremal_timestamps_of_child_objects if
                                                  timestamp is not None]

    assert len(valid_extremal_timestamps_of_child_objects) >= 1

    extremal_timestamp = python_min_max_func(valid_extremal_timestamps_of_child_objects)

    return extremal_timestamp


def _fix_time_columns_on_broken_scraping_session_rows(db_session: Session):
    with db_session.no_autoflush:
        sessions_without_time = db_session.query(ScrapingSession).filter(
            or_(ScrapingSession.time_started == None, ScrapingSession.time_finished == None)).all()

        sessions_without_start_time = [session for session in sessions_without_time if session.time_started is None]

        for session_without_start_time in sessions_without_start_time:
            start_time = _get_timestamp_on_scraping_session_row(db_session, session_without_start_time,
                                                                EXTREMAL_TIMESTAMP.LOWEST)
            session_without_start_time.time_started = start_time

        sessions_without_finish_time = [session for session in sessions_without_time if session.time_finished is None]

        for session_without_finish_time in sessions_without_finish_time:
            finish_time = _get_timestamp_on_scraping_session_row(db_session, session_without_finish_time,
                                                                 EXTREMAL_TIMESTAMP.HIGHEST)
            session_without_finish_time.time_finished = finish_time


def _get_broken_sellers(db_session: Session):
    return db_session.query(Seller).filter(Seller.registration_date == None)


def _get_broken_listings(db_session: Session):
    return db_session.query(ListingObservation).filter(ListingObservation.url == None)


def _get_scraping_sessions_with_no_children(db_session: Session):
    scraping_sessions = db_session.query(ScrapingSession).all()

    ids_scraping_sessions_with_no_children = []

    for scraping_session in scraping_sessions:
        listing_count = db_session.query(func.count(ListingObservation.id)).filter(
            ListingObservation.session_id == scraping_session.id).scalar()
        seller_observation_count = db_session.query(func.count(SellerObservation.id)).filter(
            SellerObservation.session_id == scraping_session.id).scalar()

        if listing_count + seller_observation_count == 0:
            ids_scraping_sessions_with_no_children.append(scraping_session.id)

    return db_session.query(ScrapingSession).filter(ScrapingSession.id.in_(ids_scraping_sessions_with_no_children))


def fix_integrity_of_database(db_session: Session):
    # remove incomplete sellers
    # remove incomplete listing_observations
    # remove scraping_sessions with no children
    # fix broken time columns on scraping sessions

    broken_sellers = _get_broken_sellers(db_session)
    broken_listings = _get_broken_listings(db_session)

    if len(broken_sellers.all() + broken_listings.all()) > 0:
        ans = input(
            f"{len(broken_sellers.all())} broken sellers and {len(broken_listings.all())} broken listings to be "
            f"deleted. Proceed? "
            f"(Y/N)")
        if ans == "Y":
            broken_sellers.delete()
            broken_listings.delete()
        else:
            print("Please manually ensure the integrity of the database before starting new scraping session.")
            db_session.expunge_all()
            db_session.close()
            exit()

    scraping_sessions_with_no_children = _get_scraping_sessions_with_no_children(db_session)

    scraping_sessions_with_no_children.delete(synchronize_session=False)

    _fix_time_columns_on_broken_scraping_session_rows(db_session)

    db_session.commit()


def shorten_and_sanitize_text(max_length, text):
    if len(text.encode("utf8")) <= max_length:
        return demoji.replace(bytes(text, "utf-8").decode('utf-8', 'ignore').strip())

    mxlen = max_length

    while (text.encode("utf8")[mxlen - 1] & 0xc0 == 0xc0):
        mxlen -= 1

    return demoji.replace(text.encode("utf8")[0:mxlen].decode("utf8", 'ignore').strip())


def _shorten_and_sanitize_for_text_column(text):
    return shorten_and_sanitize_text(MYSQL_TEXT_COLUMN_MAX_LENGTH, text)


def _shorten_and_sanitize_for_medium_text_column(text):
    return shorten_and_sanitize_text(MYSQL_MEDIUM_TEXT_COLUMN_MAX_LENGTH, text)


def get_column_name(column: InstrumentedAttribute) -> str:
    return column.expression._Annotated__element.description


def get_engine():
    engine = create_engine(DB_ENGINE_URL, **SQLALCHEMY_CREATE_ENGINE_KWARGS)
    return engine


def get_db_session(engine):
    Session = sessionmaker(
        bind=engine)
    db_session = Session()
    db_session.rollback()
    return db_session


def get_settings(db_session=None):
    if db_session:
        existing_settings = db_session.query(Settings).first()
    else:
        engine = get_engine()
        db_session = get_db_session(engine)
        existing_settings = db_session.query(Settings).first()
        db_session.expunge_all()
        db_session.close()

    if existing_settings:
        return existing_settings
    else:
        raise IntegrityError


def set_settings(db_session, refill_queue_when_complete=False):
    existing_settings = db_session.query(Settings).first()
    if not existing_settings:
        settings = Settings(refill_queue_when_complete=refill_queue_when_complete)
        db_session.add(settings)
        db_session.commit()
        db_session.expunge_all()
        db_session.close()