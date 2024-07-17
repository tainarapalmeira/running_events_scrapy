from scrapy import Spider, Request
from bs4 import BeautifulSoup
from laufkalender.items import RunnersWorldItem
import json
import chompjs
import jq


class EventSpider(Spider):
    name = "runnersworld"
    start_urls = [
        "https://www.runnersworld.de/laufevents-in-berlin/",
        "https://www.runnersworld.de/laufevents-in-berlin/seite/2/",
    ]

    def parse_js_script(self, response):
        try:
            response = response.text
            soup = BeautifulSoup(response, "html.parser")

            # Extract JavaScript from response
            js_script = soup.find("script", {"id": "__NEXT_DATA__"}).text

            # Convert parsed JS script object to JSON string
            js_parsed = chompjs.parse_js_object(js_script)

            js_parsed = json.dumps(js_parsed, indent=4)

            return js_parsed
        except Exception as e:
            self.logger.error(f"Error parsing JavaScript from response {e}")
            return None

    def get_event_urls(self, response, js_parsed):
        # Define jq filter: find "events" key and get its data
        jq_filter = '.. | objects | select(has("events")) | .events'

        try:
            event_data_json = jq.compile(jq_filter).input(text=js_parsed).all()
        except Exception as e:
            self.logger.error(f"Error applying jq filter: {e}")

        # Convert event data to JSON string
        event_data_json = json.dumps(event_data_json, indent=4)

        # Define jq filter: find "url" values
        jq_filter = '.. | objects | select(has("url")) | .url'

        try:
            event_urls = jq.compile(jq_filter).input(text=event_data_json).all()
        except Exception as e:
            self.logger.error(f"Error applying jq filter: {e}")

        return event_urls

    def parse_event_data(self, response):
        response = response.text
        soup = BeautifulSoup(response, "html.parser")

        # Extract JavaScript from response
        js_script = soup.find("script", {"id": "__NEXT_DATA__"}).text

        # Parse Javascript object
        # try:
        parsed_js = chompjs.parse_js_object(js_script)
        # except IndexError:
        #     self.logger.error("IndexError: Javascript index out of range")
        # except Exception as e:
        #     self.logger.error(f"Error parsing Javascript: {e}")

        # Convert parsed JS object to JSON string
        json_data = json.dumps(parsed_js, indent=4)

        # Define jq filter: find "data" key and get its data
        jq_filter = '.. | objects | select(has("mobile")) | .mobile'

        try:
            mobile_data = jq.compile(jq_filter).input(text=json_data).all()
        except Exception as e:
            self.logger.error(f"Error applying jq filter: {e}")

        # Convert event data to JSON string
        mobile_data_json = json.dumps(mobile_data, indent=4)

        # Define jq filter: find "data" key and get its data
        jq_filter = '.. | objects | select(has("data")) | .data'

        try:
            data = jq.compile(jq_filter).input(text=mobile_data_json).all()
        except Exception as e:
            self.logger.error(f"Error applying jq filter: {e}")

        #
        data = data[6]

        event = RunnersWorldItem()

        event["title"] = data["title"]
        event["description"] = data["intro"]
        event["url"] = data["url"]
        event["city"] = data["city"]
        event["address"] = (
            f"{data['zip']}, {data['street']} {data['houseNumber']} ({data['addressAdditionalInfo']})"
        )
        event["mailorganizer"] = data["mailOrganizer"]
        event["urlorganizer"] = data["urlOrganizer"]
        event["eventdate"] = data["eventDate"]
        event["distances"] = data["distances"]

        yield event

    def parse(self, response):
        # For the Runner's World website, it is easier to extract data directly from the JavaScript objects in the source code.
        # This approach simplifies parsing compared to extracting data from the rendered HTML.
        js_parsed = self.parse_js_script(response)

        event_urls = self.get_event_urls(response, js_parsed)
        for event_url in event_urls:
            yield Request(event_url, callback=self.parse_event_data)
