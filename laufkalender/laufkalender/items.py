from scrapy import Field, Item


class BerlinOfficialItem(Item):
    title = Field()
    description = Field()
    event_url = Field()
    city = Field()
    address = Field()
    organizer_email = Field()
    organizer_url = Field()
    event_date = Field()
    distances = Field()
    fee = Field()


class RunnersWorldItem(Item):
    title = Field()
    description = Field()
    event_url = Field()
    city = Field()
    address = Field()
    organizer_email = Field()
    organizer_url = Field()
    event_date = Field()
    distances = Field()
    fee = Field()
