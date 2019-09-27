from src.empire.scrape import EmpireScrapingSession

session_id = input("Session id to resume: ")
pagenr = input("Pagenr from which to start: ")
listing_nr = input("Listing_nr from which to start: ")

if session_id:
    session_id = int(session_id)

if pagenr:
    pagenr = int(pagenr)

if listing_nr:
    listing_nr = int(listing_nr)

scraping_session = EmpireScrapingSession(session_id=session_id, initial_pagenr=pagenr, initial_listingnr=listing_nr)
scraping_session.scrape()