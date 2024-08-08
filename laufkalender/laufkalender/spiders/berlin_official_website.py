from scrapy import Spider, Request


class BerlinOfficialSpider(Spider):
    name = "berlin_official"
    start_urls = ["https://www.berlin.de/special/sport-und-fitness/laufkalender/"]

    def parse_event(self, response):
        event_block = response.xpath("//div[@class='block infocontainer']/dl")

        event_fields = event_block.xpath("./dt/text()").getall()
        event_values = event_block.xpath("./dd").getall()

        event_data = {
            event_fields[i]: event_values[i] for i in range(len(event_fields))
        }

        yield event_data

    def parse(self, response):
        events = response.css("div.inner p.text")
        for event in events:
            event_link = event.css("a::attr(href)").get()
            yield response.follow(
                url=event_link,
                callback=self.parse_event,
            )
        next_page = response.xpath(
            "//nav[@class='pagination ']/ul//li//a[@class='active']/parent::*/following-sibling::li//a/@href"
        ).get()

        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield Request(next_page, callback=self.parse)
