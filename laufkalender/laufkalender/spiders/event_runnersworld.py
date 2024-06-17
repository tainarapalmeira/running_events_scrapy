from scrapy import Spider, Request
import logging
import json
import chompjs
import jq


class EventSpider(Spider):
    name = "runnersworld"
    start_urls = [
        "https://www.runnersworld.de/laufevents-in-berlin/",
        "https://www.runnersworld.de/laufevents-in-berlin/seite/2/",
    ]

    def __init__(self):
            self.event_urls_list = []

    def get_js_data(self, response):
        # Extract JavaScript from response
        javascript = response.css("script::text").getall()

        if not javascript:
            logging.log("There is no Javascript in response")

        # Parse Javascript object
        try:
            js_data = chompjs.parse_js_object(javascript[1])
        except IndexError:
            logging.log("IndexError: Javascript index out of range")
        except Exception as e:
            logging.log(f"Error parsing Javascript: {e}")

        return js_data

    def get_event_url(self, response, js_data):
        # Convert parsed JS object to JSON string
        json_data = json.dumps(js_data, indent=4)

        # Define jq filter: find "events" key and get its data
        jq_filter = '.. | objects | select(has("events")) | .events'

        try:
            events = jq.compile(jq_filter).input(text=json_data).all()
        except Exception as e:
            logging.log(f"Error applying jq filter: {e}")

        # Convert event data to JSON string
        event_data_json = json.dumps(events, indent=4)

        # Define jq filter: find "url" values
        jq_filter = '.. | objects | select(has("url")) | .url'

        try:
            event_urls = jq.compile(jq_filter).input(text=event_data_json).all()
        except Exception as e:
            logging.log(f"Error applying jq filter: {e}")

        for event in event_urls:
            if not event in self.event_urls_list:
                self.event_urls_list.append(event)

        return self.event_urls_list

    def get_event_data(self, response):
        # Extract JavaScript from response
        javascript = response.css("script::text").getall()

        if not javascript:
            logging.log("There is no Javascript in response")

        # Parse Javascript object
        try:
            parsed_js = chompjs.parse_js_object(javascript[1])
        except IndexError:
            logging.log("IndexError: Javascript index out of range")
        except Exception as e:
            logging.log(f"Error parsing Javascript: {e}")

        # Convert parsed JS object to JSON string
        json_data = json.dumps(parsed_js, indent=4)

        # Define jq filter: find "data" key and get its data
        jq_filter = '.. | objects | select(has("mobile")) | .mobile'

        try:
            mobile_data = jq.compile(jq_filter).input(text=json_data).all()
        except Exception as e:
            logging.log(f"Error applying jq filter: {e}")

        # Convert event data to JSON string
        mobile_data_json = json.dumps(mobile_data, indent=4)

        # Define jq filter: find "data" key and get its data
        jq_filter = '.. | objects | select(has("data")) | .data'

        try:
            data = jq.compile(jq_filter).input(text=mobile_data_json).all()
        except Exception as e:
            logging.log(f"Error applying jq filter: {e}")

        # Convert event data to JSON string
        foo = data[6]

        bar = {
            "title": foo["title"],
            "description": foo["intro"],
            "url": foo["url"],
            "city": foo["city"],
            "address": f"{foo['zip']}, {foo['street']} {foo['houseNumber']} ({foo['addressAdditionalInfo']})",
            "mailorganizer": foo["mailOrganizer"],
            "urlorganizer": foo["urlOrganizer"],
            "eventdate": foo["eventDate"],
            "distances": foo["distances"],
        }

        data_json = json.dumps(bar, indent=4)

        with open("event_runnersworld.json", "a") as file:
            file.write(f"{data_json}")
        file.close()

    def parse(self, response):
        # For the Runner's World website, it is easier to extract data directly from the JavaScript objects in the source code.
        # This approach simplifies parsing compared to extracting data from the rendered HTML.
        js_data = self.get_js_data(response)

        event_urls = self.get_event_url(response, js_data)
        for event_url in event_urls:
            yield Request(event_url, callback=self.get_event_data)
