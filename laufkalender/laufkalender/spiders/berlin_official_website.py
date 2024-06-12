from typing import Any
from scrapy import Spider, Request
from scrapy.http import Response


class EventSpider(Spider):
    name = "berlin_official"
    start_urls = [
        "https://www.berlin.de/special/sport-und-fitness/laufkalender/"
    ]

    def parse(self, response):
        events = response.css("div.inner p.text")
        for event in events:
            event_link = event.css("a::attr(href)").get()
            yield response.follow(
                url=event_link,
                callback=self.get_event_details,
            )
        next_page = response.xpath(
            "//nav[@class='pagination ']/ul//li//a[@class='active']/parent::*/following-sibling::li//a/@href"
        ).get()

        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield Request(next_page, callback=self.parse)

    def get_event_details(self, response):
        event_details_blocks = response.xpath("//div[@class='block infocontainer']/dl")
        for event_details_block in event_details_blocks:
            event_details_keys = event_details_block.xpath("./dt/text()").getall()
            event_details_values = event_details_block.xpath("./dd/text()").getall()

            print(f"'{event_details_keys}': event_details_values")

            event_data = {
                event_details_keys[i]: event_details_values[i]
                for i in range(len(event_details_keys))
            }

            yield event_data
