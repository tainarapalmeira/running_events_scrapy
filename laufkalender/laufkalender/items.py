from scrapy import Field, Item


class BerlinOfficialItem(Item):
    title = Field()
    description = Field()
    url = Field()
    city = Field()
    address = Field()
    mailorganizer = Field()
    urlorganizer = Field()
    eventdate = Field()
    distances = Field()
    fee = Field()
