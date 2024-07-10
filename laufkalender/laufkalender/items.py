from scrapy import Field, Item


class RunnersWorldItem(Item):
    title = Field()
    description = Field()
    url = Field()
    city = Field()
    address = Field()
    mailorganizer = Field()
    urlorganizer = Field()
    eventdate = Field()
    distances = Field()
