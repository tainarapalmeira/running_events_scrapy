import sqlite3
from datetime import datetime

def convert_event_dates_to_string(item):
    return ", ".join(item['eventdate'])
class LaufkalenderPipeline:
    def __init__(self):
        self.con = sqlite3.connect("running_events.db")
        self.cur = self.con.cursor()
        self.create_table()

    def create_table(self):
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS runnersworld(
            title TEXT,
            description TEXT,
            url TEXT,
            city TEXT,
            address TEXT,
            mailorganizer TEXT,
            urlorganizer TEXT,
            eventdate TEXT,
            distances TEXT,
            scraped_at TEXT)
            """
        )

    def process_item(self, item, spider):
        eventdate = convert_event_dates_to_string(item)
        distances = str(item['distances'][0])

        self.cur.execute(
            """INSERT OR IGNORE INTO runnersworld VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
            (item["title"],
            item["description"],
            item["url"],
            item['city'],
            item['address'],
            item['mailorganizer'],
            item['urlorganizer'],
            eventdate,
            distances,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        self.con.commit()
        return item
