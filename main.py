"""
Fetches events from Eventbrite
"""

import json
import logging
import os
import re
import time
import urllib
import uuid
from bs4 import BeautifulSoup
from curl_cffi import requests
from rich import print
from rich.logging import RichHandler

from models import EventData


class EventBriteScraper:
    """
    Scrapes events from Eventbrite
    """

    def __init__(self, url_param: str):
        """
        Initializes the scraper
        """
        logging.info("Initializing the scraper")
        self.session = self._get_session()
        self.url_param = url_param

    @classmethod
    def _get_session(cls) -> requests.Session:
        return requests.Session()

    @staticmethod
    def is_valid_event_url(url: str) -> bool:
        """
        Checks if the given URL is a valid Eventbrite URL
        """
        try:
            result = urllib.parse.urlparse(url)
            assert result.netloc in ["www.eventbrite.com", "eventbrite.com"]
            assert all([result.scheme, result.netloc, result.path])
            return True
        except (AssertionError, ValueError):
            logging.warning(f"Invalid Eventbrite URL: {url}")
            return False

    def _fetch_initial_data(self) -> tuple[str, dict]:
        """
        Fetches the initial data and CSRF token
        """
        response = self.session.get(self.url_param, impersonate="chrome")
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.select_one('input[name="csrfmiddlewaretoken"]')["value"]

        script_tag = soup.find("script", string=lambda s: s and "window.__SERVER_DATA" in s)
        json_data = re.search(r"window\.__SERVER_DATA__ = ({.*?});", script_tag.string, re.DOTALL)
        server_data = json.loads(json_data.group(1))

        return csrf_token, server_data

    def get_event_data(self) -> list[EventData]:
        """
        Fetches the event data
        """
        logging.info("Fetching the event data")
        csrf_token, server_data = self._fetch_initial_data()

        event_search_data, page_count = self._extract_server_data(server_data)

        logging.info(f"Found {page_count} pages to fetch")
        event_data = self._fetch_event_data(csrf_token, event_search_data, page_count)

        logging.info(f"Found {len(event_data)} events")
        return event_data

    @staticmethod
    def _extract_server_data(server_data: dict) -> tuple[dict, int]:
        """
        Extracts the server data from the initial data
        """
        event_search_data = server_data.get("search_data", {}).get("event_search", {})
        page_count = server_data.get("page_count", 1)

        return event_search_data, page_count

    def _fetch_event_data(self, csrf_token: str, event_search_data: dict, page_count: int) -> list[EventData]:
        """
        Fetches the event data for all pages
        """
        event_data = []

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://www.eventbrite.com/",
            "X-CSRFToken": csrf_token,
        }

        logging.info(f"Fetching event data for {page_count} pages")
        for i in range(1, page_count + 1):
            event_data.extend(self._fetch_event_data_for_page(event_search_data, headers, i))
            time.sleep(2)

        return event_data

    def _fetch_event_data_for_page(self, event_search_data: dict, headers: dict, page: int) -> list[EventData]:
        """
        Fetches the event data for a single page
        """
        payload = {
            "event_search": event_search_data,
            "debug_experiment_overrides": {"search_exp_4": "D"},
            "browse_surface": "search",
        }
        payload["event_search"]["page"] = page

        logging.info(f"Fetching event data for page {page}")
        response = self.session.post(
            "https://www.eventbrite.com/api/v3/destination/search/", json=payload, headers=headers
        )
        event_data_results = response.json().get("events", {}).get("results", [])

        logging.info(f"Found {len(event_data_results)} events in page {page}")
        event_data_list = []
        for event_data_result in event_data_results:
            event_url = event_data_result.get("url")
            logging.info(f"Getting event data from {event_url}")

            response = self.session.get(event_url, impersonate="chrome")

            if response.status_code != 200:
                logging.warning(f"Failed to get event data from {event_url}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            event_data_el = soup.find_all("script", type="application/ld+json")[1]
            event_data = json.loads(event_data_el.text)

            event_data_list.append(
                EventData(
                    event_name=event_data_result.get("name"),
                    date_time={
                        "start_date": event_data_result.get("start_date"),
                        "start_time": event_data_result.get("start_time"),
                        "end_date": event_data_result.get("end_date"),
                        "end_time": event_data_result.get("end_time"),
                    },
                    event_url=event_url,
                    location=event_data["location"].get("address", {}).get("streetAddress", ""),
                    prices=[
                        {
                            "name": offer.get("name", ""),
                            "price": str(offer.get("price", "")),
                        }
                        for offer in event_data.get("offers", [])
                        if offer.get("name", "") or offer.get("price", "")
                    ],
                )
            )

        return event_data_list


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])

    input_url = input("> Enter the Eventbrite URL: ")

    if not EventBriteScraper.is_valid_event_url(input_url):
        logging.error("Invalid Eventbrite URL")
        exit(1)

    scraper = EventBriteScraper(url_param=input_url)
    event_data = scraper.get_event_data()

    # Save the event data to a JSON file
    file_path = "event_datas/event_data_" + str(uuid.uuid4().hex[:5]) + ".json"
    logging.info(f"Saving the event data to {file_path}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w+") as f:
        json.dump([event_data.model_dump() for event_data in event_data], f, indent=4, ensure_ascii=False)
