from bs4 import BeautifulSoup
from datetime import datetime
import logging
import requests
import json


class LaufkalenderPipeline:
    # support function to runnersworld spider items
    def convert_event_dates_to_string(self, item):
        return ", ".join(item["eventdate"])

    # support function to berlin_official spider items
    def clean_data(self, data):
        if not isinstance(data, str):
            return data
        soup = BeautifulSoup(data, "html.parser")
        return soup.get_text()

    def process_item(self, item, spider):
        url = f"http://localhost:8000/create_event/"
        if spider.name == "berlin_official":
            event = {}

            event_item_fields = {
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
            event_item_keys = list(event_item_fields.keys())

            for key in event_item_keys:
                for field in item:
                    if field in event_item_fields[key]:
                        data = self.clean_data(item[field])
                        event[key] = data
                        break
                    elif field not in event_item_fields[key]:
                        event[key] = ""
            if event["title"]:
                event.update(
                    scraped_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    spider="berlin_official",
                )

        if spider.name == "runnersworld":

            event = {
                "title": item["title"],
                "description": item["description"],
                "url": item["url"],
                "city": item["city"],
                "address": item["address"],
                "mailorganizer": item["mailorganizer"],
                "urlorganizer": item["urlorganizer"],
                "eventdate": self.convert_event_dates_to_string(item),
                "distances": str(item["distances"][0]),
                "fee": "",  # Temporário
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "spider": "runnersworld",
            }

        payload_json = json.dumps(event)
        try:
            response = requests.post(url, data=payload_json)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.exception(f"Resquest failed: {e}\nFrom event({payload_json.title})")
        return
