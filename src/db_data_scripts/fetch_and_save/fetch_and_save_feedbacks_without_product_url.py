import pickle

from src.db_utils import get_engine, get_db_session
from src.models.feedback import Feedback

engine = get_engine()

db_session = get_db_session(engine)

feedbacks_where_url_is_none = db_session.query(Feedback).filter(Feedback.product_url == None).all()
print(f"fetched feedbacks, {len(feedbacks_where_url_is_none)}")
with open("../pickle_data/feedbacks_where_url_is_none.pickle", "wb") as f:
    pickle.dump(feedbacks_where_url_is_none, f)