from laufkalender.items import BerlinOfficialItem, RunnersWorldItem
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import logging


class CleanDataPipeline:
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
        if spider.name == "berlin_official":
            event = BerlinOfficialItem()

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
                        event[key] = None
            return event
        elif spider.name == "runnersworld":
            event = RunnersWorldItem()

            event["title"] = item["title"]
            event["description"] = item["description"]
            event["url"] = item["url"]
            event["city"] = item["city"]
            event["address"] = item["address"]
            event["mailorganizer"] = item["mailorganizer"]
            event["urlorganizer"] = item["urlorganizer"]
            event["eventdate"] = self.convert_event_dates_to_string(item)
            event["distances"] = str(item["distances"][0])
            event["fee"] = None  # Temporário
            # event["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            return event


class LaufkalenderPipeline:
    def open_spider(self, spider):
        self.connection = sqlite3.connect("running_events.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS berlinofficial(
                title TEXT,
                description TEXT,
                url TEXT,
                city TEXT,
                address TEXT,
                mailorganizer TEXT,
                urlorganizer TEXT,
                eventdate TEXT,
                distances TEXT,
                fee TEXT,
                scraped_at TEXT
                )
        """
        )
        self.connection.commit()

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        try:
            # Check if is there any event with the same name before storing it in the db
            result = self.cursor.execute(
                "SELECT title FROM berlinofficial WHERE title=?", (item["title"],)
            ).fetchone()

            if result:
                logging.info(f"Duplicate event was found: {result}")
                return None

            self.cursor.execute(
                """
                INSERT INTO berlinofficial (
                    title, description, url, city, address, mailorganizer, urlorganizer, eventdate, distances, fee, scraped_at
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["title"],
                    item["description"],
                    item["url"],
                    item["city"],
                    item["address"],
                    item["mailorganizer"],
                    item["urlorganizer"],
                    item["eventdate"],
                    item["distances"],
                    item["fee"],
                    datetime.now().isoformat(),
                ),
            )
            self.connection.commit()
        except sqlite3.Error as err:
            logging.error("sqlite3 error: %s" % (" ".join(err.args)))
            logging.error("Exception class is: ", err.__class__)
        except Exception as err:
            logging.error(f"An error ocurred: {err}")
        return item
