EMPIRE_MARKET_URL = "empiremktxgjovhm.onion"
IMAGE_CAPTCHA_URL_REGEX = r"http:\/\/"+EMPIRE_MARKET_URL.replace(".", "\.")+"\/public\/captchaimg\/[0-9]{10}\.[0-9]{3}\.jpg"
TOR_PORT = 9050

PROXIES = {
    'http': "socks5h://localhost:{}".format(TOR_PORT),
    'https': "socks5h://localhost:{}".format(TOR_PORT)
}