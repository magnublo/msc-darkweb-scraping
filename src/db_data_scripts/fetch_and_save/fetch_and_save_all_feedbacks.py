import pickle

from src.db_data_scripts.utils import generate_output_file_name
from src.db_utils import get_engine, get_db_session
from src.models.feedback import Feedback

engine = get_engine()

db_session = get_db_session(engine)

feedbacks = db_session.query(Feedback).all()

print(f"fetched feedbacks, {len(feedbacks)}")

output_file_name = generate_output_file_name(suffix="all_feedbacks", entries=feedbacks)

with open(output_file_name, "wb") as f:
    pickle.dump(feedbacks, f)