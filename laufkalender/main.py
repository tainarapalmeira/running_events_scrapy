from laufkalender.spiders.runnersworld_website import RunnersWorldSpider
from laufkalender.spiders.berlin_official_website import BerlinOfficialSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(RunnersWorldSpider)
    process.crawl(BerlinOfficialSpider)
    process.start()


if __name__ == "__main__":
    main()
