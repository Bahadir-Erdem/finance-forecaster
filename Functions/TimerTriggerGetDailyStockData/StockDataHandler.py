from . import Database, Date, Time, StockDataFetcher
from .Database import Database
from .Date import Date
from .Time import Time
from .StockDataFetcher import StockDataFetcher
import pandas as pd

class StockDataHandler:
    def __init__(self, database: Database) -> None:
        self.conn = database.conn
        self.engine = database.engine
        self.date = Date(database)
        self.time = Time(database)
        self.stocks_df = StockDataFetcher().fetch()
    
    def fetch_and_to_db(self):
        for index, row in self.stocks_df.iterrows():
            self.date.set_date_id(row)
            self.time.set_time_id(row)
            self.insert_or_update_stock_data(row)
            self.insert_or_update_stock_data_ft(row)
    
    
    def insert_or_update_stock_data(self, row):
        cursor = self.conn.cursor()
        TABLE_NAME = 'dim_stock_t'
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{TABLE_NAME}'")
        column_names = [row[0] for row in cursor.fetchall()]
        stock_data = row[column_names]

        sql_insert = """
        INSERT INTO dbo.dim_stock_t ({})
        VALUES ({})
        """.format(', '.join(column_names), ', '.join(['?'] * len(column_names)))


        sql_check = """
        SELECT * FROM dbo.dim_stock_t
        WHERE {}
        """.format(' AND '.join(['{} = ?'.format(column_name) for column_name in column_names]))

        cursor.execute(sql_check, tuple(stock_data))
        result = cursor.fetchone()

        if result is None:
            cursor.execute(sql_insert, tuple(stock_data))

        self.conn.commit()

        cursor.close()

    def insert_or_update_stock_data_ft(self, row):
        TABLE_NAME = 'ft_stock_price_t'
        query = f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{TABLE_NAME}'"
        column_names = pd.read_sql(query, self.engine)['column_name'].tolist()
        row_df = pd.DataFrame([row], columns=column_names)
        row_df.to_sql(TABLE_NAME, self.engine, index=False, if_exists='append')    