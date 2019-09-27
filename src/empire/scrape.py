import hashlib
import time
import traceback

import requests
from requests.cookies import create_cookie

from definitions import EMPIRE_MARKET_URL, EMPIRE_MARKET_ID, DEBUG_MODE, EMPIRE_BASE_CRAWLING_URL, EMPIRE_DIR, \
    EMPIRE_MARKET_LOGIN_URL, PROXIES
from src.base import Base, engine, db_session, LoggedOutException
from src.base import BaseScraper
from src.empire.functions import EmpireScrapingFunctions as scrapingFunctions
from src.models.country import Country
from src.models.listing_category import ListingCategory
from src.models.listing_observation import ListingObservation
from src.models.listing_observation_category import ListingObservationCategory
from src.models.listing_observation_country import ListingObservationCountry
from src.models.listing_text import ListingText

NR_OF_PAGES = 2249

Base.metadata.create_all(engine)


class EmpireScrapingSession(BaseScraper):

    @staticmethod
    def _is_logged_out(response):
        for history_response in response.history:
            if history_response.is_redirect:
                if history_response.raw.headers._container['location'][1] == EMPIRE_MARKET_LOGIN_URL:
                    return True

        return False

    def _handle_logged_out_session(self):
        if self.logged_out_exceptions >= 5:
            raise LoggedOutException()
        else:
            self.logged_out_exceptions += 1

    def __init__(self, session_id=None, initial_pagenr=0, initial_listingnr=0):
        super().__init__(session_id=session_id)
        self.initial_pagenr = initial_pagenr
        self.initial_listingnr = initial_listingnr
        self.logged_out_exceptions = 0

    def _get_working_dir(self):
        return EMPIRE_DIR

    def _login_and_set_cookie(self):

        self.web_session.cookies.set_cookie(
            create_cookie(
            name='ab',
            value='1cc735432450e28fa3333f2904cd5ae3')
        )

        self.web_session.cookies.set_cookie(
            create_cookie(
                name='shop',
                value='39o8ljpgfjspkliioqg0pq4632dodiqi')
        )

    def _get_market_URL(self):
        return EMPIRE_MARKET_URL

    def _get_market_ID(self):
        return EMPIRE_MARKET_ID

    def _get_headers(self):
        return {
            "Host": self._get_market_URL(),
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "http://" + self._get_market_URL() + "/login",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def scrape(self):

        pagenr = self.initial_pagenr
        k = self.initial_listingnr

        while pagenr < NR_OF_PAGES:

            try:
                search_result_url = EMPIRE_BASE_CRAWLING_URL + str((pagenr - 1) * 15)
                soup_html = self._get_page_as_soup_html(search_result_url, file="saved_empire_search_result_html")
                product_page_urls, urls_is_sticky = scrapingFunctions.get_product_page_urls(soup_html)
                titles, sellers = scrapingFunctions.get_titles_and_sellers(soup_html)
                btc_rate, ltc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)

                while k < len(product_page_urls):
                    title = titles[k]
                    seller = sellers[k]

                    existing_listing_observation = db_session.query(ListingObservation).filter_by(
                        title=title,
                        seller=seller,
                        session_id=self.session_id
                    ).first()

                    if existing_listing_observation:
                        print("Database already contains listing with this seller and title for this session.")
                        print("Seller: " + existing_listing_observation.seller)
                        print("Listing title: " + existing_listing_observation.title)
                        print("Duplicate listing, skipping...")
                        print("Crawling listing nr " + str(pagenr * 15 + k) + " this session. " + str(
                            self.duplicates_this_session) + " duplicates encountered.")
                        print("\n")
                        self.duplicates_this_session += 1
                        k += 1
                        continue


                    product_page_url = product_page_urls[k]
                    print(time.time())
                    print("Trying to fetch URL: " + product_page_url)
                    print("On pagenr " + str(pagenr) + " and item nr " + str(k) + ".")
                    print("Crawling listing nr " + str(pagenr*15+k) + " this session. " + str(self.duplicates_this_session) + " duplicates encountered.")
                    print("\n")
                    soup_html = self._get_page_as_soup_html(product_page_url, 'saved_empire_html', DEBUG_MODE)

                    session_id = self.session_id
                    listing_text = scrapingFunctions.get_description(soup_html)
                    listing_text_id = hashlib.md5(listing_text.encode('utf-8')).hexdigest()
                    categories, website_category_ids = scrapingFunctions.get_categories_and_ids(soup_html)
                    accepts_BTC, accepts_LTC, accepts_XMR = scrapingFunctions.accepts_currencies(soup_html)
                    nr_sold, nr_sold_since_date = scrapingFunctions.get_nr_sold_since_date(soup_html)
                    fiat_currency, price = scrapingFunctions.get_fiat_currency_and_price(soup_html)
                    origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)
                    vendor_level, trust_level = scrapingFunctions.get_vendor_and_trust_level(soup_html)

                    is_sticky = urls_is_sticky[k]

                    db_category_ids = []

                    for i in range(0, len(categories)):
                        category = db_session.query(ListingCategory).filter_by(
                            website_id=website_category_ids[i],
                            name=categories[i],
                            market=self.market_id).first()

                        if not category:
                            category = ListingCategory(
                                website_id=website_category_ids[i],
                                name=categories[i],
                                market=self.market_id
                            )
                            db_session.add(category)
                            db_session.flush()

                        db_category_ids.append(category.id)

                    db_session.merge(ListingText(
                        id=listing_text_id,
                        text=listing_text
                    ))

                    db_session.merge(Country(
                        id=origin_country
                    ))

                    db_session.flush()

                    listing_observation = ListingObservation(
                        session_id=session_id,
                        listing_text_id=listing_text_id,
                        title=title,
                        btc=accepts_BTC,
                        ltc=accepts_LTC,
                        xmr=accepts_XMR,
                        promoted_listing=is_sticky,
                        seller=seller,
                        btc_rate=btc_rate,
                        ltc_rate=ltc_rate,
                        xmr_rate=xmr_rate,
                        nr_sold=nr_sold,
                        nr_sold_since_date=nr_sold_since_date,
                        fiat_currency=fiat_currency,
                        price=price,
                        origin_country=origin_country,
                        vendor_level=vendor_level,
                        trust_level=trust_level
                    )

                    db_session.add(listing_observation)

                    db_session.flush()

                    for destination_country in destination_countries:
                        db_session.merge(Country(
                            id=destination_country
                        ))

                        db_session.flush()

                        db_session.add(ListingObservationCountry(
                            listing_observation_id=listing_observation.id,
                            country_id=destination_country
                        ))

                    for db_category_id in db_category_ids:
                        db_session.add(ListingObservationCategory(
                            listing_observation_id=listing_observation.id,
                            category_id=db_category_id
                        ))


                    db_session.commit()
                    k += 1
                    self.logged_out_exceptions = 0

                pagenr += 1
                k = 0

            except (KeyboardInterrupt, SystemExit, AttributeError, LoggedOutException):
                self._wrap_up_session()
                debug_html = None
                tries = 0
                while debug_html is None and tries < 10:
                    try:
                        debug_html = requests.get(EMPIRE_BASE_CRAWLING_URL, proxies=PROXIES, headers=self.headers).text
                        debug_html = "".join(debug_html.split())
                    except:
                        tries += 1
                print(debug_html)
                raise
            except BaseException as e:
                traceback.print_exc()
                print("Error on pagenr " + str(pagenr) + " and item nr " + str(k) + ".")
                print("Retrying ...")
                print("Rolled back to pagenr " + str(pagenr) + " and item nr " + str(k) + ".")

        self._wrap_up_session()

