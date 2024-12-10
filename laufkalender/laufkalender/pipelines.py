from scrapy.exceptions import DropItem
from bs4 import BeautifulSoup
from datetime import datetime
import dateparser
import logging
import requests


class LaufkalenderPipeline:
    def __init__(self):
        self.api_url = f"http://localhost:8000/event/"

    def parse_and_format_date(self, eventdate_item):
        parsed_date = dateparser.parse(eventdate_item)
        if parsed_date:
            return parsed_date.strftime("%d/%m/%Y")

    def convert_event_dates_to_string(self, eventdate, spider):
        try:
            if isinstance(eventdate, list):
                parsed_date_list = [
                    self.parse_and_format_date(eventdate_item)
                    for eventdate_item in eventdate
                ]
                parsed_date_str = ",".join(parsed_date_list)
                return parsed_date_str
            elif isinstance(eventdate, str):
                return self.parse_and_format_date(eventdate)
            else:
                raise TypeError(
                    f"Unsupported type for eventdate: {eventdate} - {spider}"
                )
        except Exception as e:
            logging.exception(f"Error converting event dates: {e} - {spider}")
            return None

    # Support function for berlin_official to retrieve content and remove HTML tags.
    def clean_data(self, data):
        if not isinstance(data, str):
            return data
        soup = BeautifulSoup(data, "html.parser")
        return soup.get_text()

    # Support function to dynamically structure data from the berlin_official spider into standardized fields.
    def map_fields(self, item, field_mapping):
        mapped_event = {}

        for key, possible_fields in field_mapping.items():
            for field in possible_fields:
                if field in item:
                    mapped_event[key] = self.clean_data(item[field])
                    break
            else:
                mapped_event[key] = ""

        return mapped_event

    def create_event_payload(self, item, spider):
        if spider.name == "berlin_official":
            field_mapping = {
                "title": ["Event", "Laufevent", "Laufkalender"],
                "description": [],
                "url": [],
                "city": [],
                "address": ["Start und Ziel", "Location", "Start"],
                "mailorganizer": [],
                "urlorganizer": ["Anmeldung & Information"],
                "eventdate": ["Beginn", "Startzeit", "Startzeiten", "Termin"],
                "distances": ["Strecke", "Streckenverlauf"],
                "fee": ["Startgebühr", "Eintritt"],
            }
            event = self.map_fields(item, field_mapping)

            if not event.get("title"):
                raise DropItem("From Berlin_official spider: Missing event title")

            event["eventdate"] = self.convert_event_dates_to_string(
                event["eventdate"], spider.name
            )
            event.update(
                scraped_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                spider="berlin_official",
            )
            return event

        elif spider.name == "runnersworld":
            event = {
                "title": item["title"],
                "description": item["description"],
                "url": item["url"],
                "city": item["city"],
                "address": item["address"],
                "mailorganizer": item["mailorganizer"],
                "urlorganizer": item["urlorganizer"],
                "eventdate": self.convert_event_dates_to_string(
                    item["eventdate"], spider.name
                ),
                "distances": str(item["distances"]),
                "fee": "",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "spider": "runnersworld",
            }
            return event
        else:
            logging.warning(f"Unknown spider: {spider.name}")
            return None

    def post_to_api(self, payload):
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(
                f"Failed to post event: {payload.get('title', 'Unknown')} | Error: {e}"
            )

    def process_item(self, item, spider):
        try:
            payload = self.create_event_payload(item, spider)
            if payload:
                self.post_to_api(payload)
        except Exception as e:
            logging.exception(f"Error processing item: {e}")
