MYSQL_ECHO_DEBUG = False
DEBUG_MODE = True
TOR_PORT = 9050
PROXIES = {
    'http': "socks5h://localhost:{}".format(TOR_PORT),
    'https': "socks5h://localhost:{}".format(TOR_PORT)
}
DB_USERNAME = "msc-scraper"
DB_ENGINE_BASE_URL = 'mysql+mysqlconnector://' + DB_USERNAME + ':Password123!@localhost:3306/magnublo_scraping'

LOCAL_ENVIRONMENT_HANDLERS = {}