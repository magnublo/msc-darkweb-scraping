import hashlib
import time

from urllib3.exceptions import ProtocolError

from definitions import EMPIRE_MARKET_URL, EMPIRE_MARKET_ID, DEBUG_MODE, EMPIRE_BASE_CRAWLING_URL, EMPIRE_DIR
from src.base import Base, engine, db_session
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

    def __init__(self):
        super().__init__()

    def _get_working_dir(self):
        return EMPIRE_DIR

    def _login_and_set_cookie(self):
        return {
            'ab': "1cc735432450e28fa3333f2904cd5ae3",
            'shop': "2fdd2i4i2337anpn4bckvqnkqcuj61u3"
        }

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
            "Cookie": "ab=" + self.cookies['ab'] + ";shop=" + self.cookies['shop'] + ";",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def scrape(self):

        for pagenr in range(1, NR_OF_PAGES):

            try:
                search_result_url = EMPIRE_BASE_CRAWLING_URL + str((pagenr - 1) * 15)
                soup_html = self._get_page_as_soup_html(search_result_url, file="saved_empire_search_result_html")
                product_page_urls = scrapingFunctions.get_product_page_urls(soup_html)
                btc_rate, ltc_rate, xmr_rate = scrapingFunctions.get_cryptocurrency_rates(soup_html)

                for product_page_url in product_page_urls:
                    soup_html = self._get_page_as_soup_html(product_page_url, 'saved_empire_html', DEBUG_MODE)

                    session_id = self.session_id
                    listing_text = scrapingFunctions.get_description(soup_html)
                    listing_text_id = hashlib.md5(listing_text.encode('utf-8')).hexdigest()
                    title = scrapingFunctions.get_title(soup_html)
                    categories, website_category_ids = scrapingFunctions.get_categories_and_ids(soup_html)
                    accepts_BTC, accepts_LTC, accepts_XMR = scrapingFunctions.accepts_currencies(soup_html)
                    seller, nr_sold, nr_sold_since_date = scrapingFunctions.get_seller_nr_sold_and_date(soup_html)
                    fiat_currency, price = scrapingFunctions.get_fiat_currency_and_price(soup_html)
                    origin_country, destination_countries = scrapingFunctions.get_origin_country_and_destinations(soup_html)
                    vendor_level, trust_level = scrapingFunctions.get_vendor_and_trust_level(soup_html)


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

                    db_session.add(self.session)

                    db_session.flush()

                    listing_observation = ListingObservation(
                        session_id=session_id,
                        listing_text_id=listing_text_id,
                        title=title,
                        btc=accepts_BTC,
                        ltc=accepts_LTC,
                        xmr=accepts_XMR,
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

            except ProtocolError:
                print(ProtocolError)
                pagenr -= 1

        self.session.time_finished = time.time()
        db_session.commit()

