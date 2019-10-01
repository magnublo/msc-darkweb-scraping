import sys
from multiprocessing import Queue

from definitions import DEBUG_MODE
from src.empire.scrape import EmpireScrapingSession

if not DEBUG_MODE:
    session_id = input("Session id to resume: ")
    pagenr = input("Pagenr from which to start: ")
    listing_nr = input("Listing_nr from which to start: ")

    if session_id:
        session_id = int(session_id)
    else:
        session_id = None

    if pagenr:
        pagenr = int(pagenr)
    else:
        pagenr = 1

    if listing_nr:
        listing_nr = int(listing_nr)
    else:
        listing_nr = 0
else:
    session_id = None
    pagenr = 1
    listing_nr = 0

queue = Queue()

scraping_session = EmpireScrapingSession(queue, username="using_python3", password="Password123!", session_id=session_id, initial_pagenr=pagenr, initial_listingnr=listing_nr)
scraping_session.populate_queue()
print(scraping_session.queue.qsize())

scraping_session.scrape()