from . import Database
from datetime import datetime
from pytz import timezone

class Date:
    def __init__(self, database: Database) -> None:
        self.conn = database.conn
        self.engine = database.engine
        default_timezone = timezone('Turkey')
        self.now = datetime.now(default_timezone)
    
    def get_current_quarter(self, datetime_value: datetime = None):
        current_date = datetime_value or self.now
        quarter = (current_date.month - 1) // 3 + 1 
        return quarter
    
    def get_current_date(self, datetime_value: datetime = None):
        now = datetime_value or self.now

        return {
            'date' : datetime.date(now),
            'day' : now.day,
            'week' : now.weekday(),
            'month' : now.month,
            'quarter' : self.get_current_quarter(now),
            'year' : now.year,
        }

    def insert_date(self, datetime: datetime):
        cursor = self.conn.cursor()

        date_data = self.get_current_date(datetime)
        DATE_TABLE_NAME = 'dim_date_t'
        columns = ', '.join(date_data.keys())
        values = ', '.join(['?' for _ in date_data])
        sql_query = f'INSERT INTO {DATE_TABLE_NAME} ({columns}) VALUES ({values})'

        cursor.execute(sql_query, tuple(date_data.values()))
        self.conn.commit()
        cursor.close()

    def set_date_id(self, row):
        datetime_value = row['datetime']
        current_date = self.get_current_date(datetime_value).get('date')
        cursor = self.conn.cursor()

        GET_EXISTING_DATE_QUERY = """
            SELECT date_id
            FROM dim_date_t
            WHERE date = ?
        """

        GET_NEWEST_ID_QUERY = """
            SELECT MAX(date_id) AS max_id
            FROM dim_date_t
        """

        try:
            cursor.execute(GET_EXISTING_DATE_QUERY, (str(current_date),))
            existing_date_id = cursor.fetchone()

            if existing_date_id is not None:
                date_id = existing_date_id[0]
            else:
                self.insert_date(datetime_value)
                cursor.execute(GET_NEWEST_ID_QUERY)
                date_id = cursor.fetchone()[0]

            self.conn.commit()  # Commit the transaction
            
            row['date_id'] = date_id

        except Exception as e:
            self.conn.rollback()  # Rollback the transaction in case of an error
            raise e