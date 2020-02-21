from src.db_utils import get_engine, get_db_session
from src.models.feedback import Feedback

engine = get_engine()

db_session = get_db_session(engine)

feedbacks_without_product_title = db_session.query(Feedback.product_url).filter(Feedback.product_title == None).all()
print(f"fetched feedbacks, {len(feedbacks_without_product_title)}")
with open("feedback_urls_where_product_title_is_none.pickle", "wb") as f:
    f.write(feedbacks_without_product_title)