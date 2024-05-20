from . import Database
from datetime import datetime
from pytz import timezone


class Time:
    def __init__(self, database: Database) -> None:
        self.conn = database.conn
        self.engine = database.engine
        self.default_timezone = timezone('Turkey')
        self.now = datetime.now(self.default_timezone)

    def get_time(self, datetime_value: datetime = None):
        now = datetime_value or self.now()

        return {
            'time' : now.time(),
            'hour' : now.hour,
            'minute' : now.minute,
            'second' : now.second
        }
    
    def insert_time(self, time_collection):
        cursor = self.conn.cursor()

        TIME_TABLE_NAME = 'dim_time_t'
        columns = ', '.join(time_collection.keys())
        placeholders = ', '.join(['?' for _ in time_collection])
        sql_query = f"INSERT INTO {TIME_TABLE_NAME} ({columns}) VALUES ({placeholders})"

        cursor.execute(sql_query, tuple(time_collection.values()))
        self.conn.commit()
        
        GET_NEWEST_ID_QUERY = 'SELECT @@IDENTITY AS ID;'
        cursor = self.conn.cursor()
        time_id = cursor.execute(GET_NEWEST_ID_QUERY).fetchone()[0]
        cursor.close()

        return time_id
    
    def set_time_id(self, row):
        datetime_value = row['datetime']
        cursor = self.conn.cursor()
        cursor.execute("SELECT time_id FROM dim_time_t WHERE time = ?", (datetime_value.time(),))
        existing_row = cursor.fetchone()
        
        if existing_row:
            # Row already exists, retrieve the ID
            time_id = existing_row[0]
        else:
            # Row does not exist, insert it into the database
            time_collection = self.get_time(datetime_value)
            time_id = self.insert_time(time_collection)

        row['time_id'] = time_id
    
    