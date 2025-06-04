from scrapy.exceptions import DropItem
from bs4 import BeautifulSoup
from datetime import datetime
import dateparser
import logging
import requests


class LaufkalenderPipeline:
    def __init__(self):
        self.api_url = f"http://localhost:8000/create_event/"

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

    # Support function for runnersworld to distances
    def parse_distances(self, distance):
        distance = [distance_item["Distanz"] for distance_item in distance]
        str_distance = "/".join(distance)
        return str_distance

    # Support function for runnersworld to parse fee
    def parse_fee(self, fee):
        fee = [fee_item["Startgebuehr"] for fee_item in fee]
        str_fee = "/".join(fee)
        return str_fee

    def create_event_payload(self, item, spider):
        if spider.name == "berlin_official":
            field_mapping = {
                "title": ["Event", "Laufevent", "Laufkalender"],
                "description": [],
                "event_url": [],
                "city": [],
                "address": ["Start und Ziel", "Location", "Start"],
                "organizer_email": [],
                "organizer_url": ["Anmeldung & Information"],
                "event_date": ["Beginn", "Startzeit", "Startzeiten", "Termin"],
                "distances": ["Strecke", "Streckenverlauf"],
                "fee": ["Startgebühr", "Eintritt"],
            }
            event = self.map_fields(item, field_mapping)

            if not event.get("title"):
                raise DropItem("From Berlin_official spider: Missing event title")

            event["event_date"] = self.convert_event_dates_to_string(
                event["event_date"], spider.name
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
                "event_url": item["event_url"],
                "city": item["city"],
                "address": item["address"],
                "organizer_email": item["organizer_email"],
                "organizer_url": item["organizer_url"],
                "event_date": self.convert_event_dates_to_string(
                    item["event_date"], spider.name
                ),
                "distances": self.parse_distances(item["distances"]),
                "fee": self.parse_fee(item["distances"]),
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "spider": "runnersworld",
            }
            print(event)
            return event
        else:
            logging.warning(f"Unknown spider: {spider.name}")
            return None

    def post_to_api(self, payload):
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to post event: {payload} | Error: {e}")

    def process_item(self, item, spider):
        try:
            payload = self.create_event_payload(item, spider)
            if payload:
                self.post_to_api(payload)
        except Exception as e:
            logging.exception(f"Error processing item: {e}")
