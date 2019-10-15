DEBUG_MODE = False
TOR_PORT = 9050
PROXIES = {
    'http': "socks5h://sikkerhetshull.no:{}".format(TOR_PORT),
    'https': "socks5h://sikkerhetshull.no:{}".format(TOR_PORT)
}
DB_USERNAME = "magnublo"
DB_ENGINE_URL = 'mysql+mysqlconnector://'+DB_USERNAME+':Password123!@mysql.stud.ntnu.no:3306/magnublo_scraping'