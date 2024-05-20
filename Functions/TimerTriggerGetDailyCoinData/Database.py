import time
import pyodbc
from .Entity import CoinData, CoinPriceData, Date, Time
import logging

class Database:
    def __init__(self, server, database, username, password, driver):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.conn_str = f'{self.driver};Server={self.server},1433;Database={self.database};Uid={self.username};Pwd={self.password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=300;'
        self.max_retry_attempts = 3
        self.retry_delay = 30  # seconds

    def connect(self):
        retry_count = 0
        last_error = None

        while retry_count < self.max_retry_attempts:
            try:
                self.conn = pyodbc.connect(self.conn_str)
                return self.conn
            except pyodbc.Error as error:
                retry_count += 1
                time.sleep(self.retry_delay)

        if last_error is not None:
            logging.error(f"Failed to establish a database connection after multiple retries. Error: {last_error}")
            return None

    def close(self):
        self.conn.close()

    def insert_time(self, time: Time):
        cursor = self.conn.cursor()

        TIME_TABLE_NAME = 'dim_time_t'
        columns = ', '.join(time.get_current_time().keys())
        values = ', '.join('?' for _ in time.get_current_time())
        sql_query = f'INSERT INTO {TIME_TABLE_NAME} ({columns}) VALUES ({values})'

        cursor.execute(sql_query, tuple(time.get_current_time().values()))
        self.conn.commit()

        GET_NEWEST_ID_QUERY = 'SELECT @@IDENTITY AS ID;'
        cursor = self.conn.cursor()
        id = cursor.execute(GET_NEWEST_ID_QUERY).fetchone()[0]
        cursor.close()
        return id
    
    def insert_date(self, date: Date):
        current_date = date.get_current_date().get('date')
        cursor = self.conn.cursor()

        GET_NEWEST_DATE_QUERY = '''
            SELECT TOP (1) date
            FROM dbo.dim_date_t
            ORDER BY date_id DESC;
        '''
        GET_NEWEST_ID_QUERY =  '''
            SELECT TOP (1) date_id
            FROM dbo.dim_date_t
            ORDER BY date_id DESC;
        '''
        cursor.execute(GET_NEWEST_DATE_QUERY)
        newest_date = cursor.fetchone()
        
        if newest_date is None:
            self.add_date(date)
            id = cursor.execute(GET_NEWEST_ID_QUERY).fetchone()[0]
            cursor.close()
            return id
        elif current_date == newest_date[0]:
            id = cursor.execute(GET_NEWEST_ID_QUERY).fetchone()[0]
            cursor.close()
            return id
        else:
            self.add_date(date)
            id = cursor.execute(GET_NEWEST_ID_QUERY).fetchone()[0]
            cursor.close()
            return id
        
    def add_date(self, date: Date):
        cursor = self.conn.cursor()

        date = date.get_current_date()
        DATE_TABLE_NAME = 'dim_date_t'
        columns = ', '.join(date.keys())
        values = ', '.join('?' for _ in date)
        sql_query = f'INSERT INTO {DATE_TABLE_NAME} ({columns}) VALUES ({values})'

        cursor.execute(sql_query, tuple(date.values()))
        self.conn.commit()
        cursor.close()
    
    def insert_or_update_coin_data(self, coin_data: CoinData):
        coins_df = coin_data.get_coin_data()
        cursor = self.conn.cursor()
        TABLE_NAME = 'dbo.dim_coin_t'
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'dim_coin_t'")
        column_names = [row[0] for row in cursor.fetchall()]
        coins_df = coins_df.loc[:, column_names]

        sql_insert = """
        INSERT INTO dbo.dim_coin_t ({})
        VALUES ({})
        """.format(', '.join(column_names), ', '.join(['?'] * len(column_names)))


        sql_check = """
        SELECT * FROM dbo.dim_coin_t
        WHERE {}
        """.format(' AND '.join(['{} = ?'.format(column_name) for column_name in column_names]))


        for index, row in coins_df.iterrows():
            cursor.execute(sql_check, tuple(row))
            result = cursor.fetchone()

            if result is None:
                cursor.execute(sql_insert, tuple(row))

        self.conn.commit()

        cursor.close()

    def insert_or_update_coin_data_ft(self, coin_price_data: CoinPriceData):
        coin_price_df = coin_price_data.get_coins_price()
        cursor = self.conn.cursor()
        TABLE_NAME = 'ft_coin_price_t'
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ft_coin_price_t'")
        column_names = [row[0] for row in cursor.fetchall()]
        coin_price_df = coin_price_df.loc[:, column_names]

        sql_insert = """
        INSERT INTO dbo.ft_coin_price_t ({})
        VALUES ({})
        """.format(', '.join(column_names), ', '.join(['?'] * len(column_names)))

        for index, row in coin_price_df.iterrows():
            cursor.execute(sql_insert, tuple(row))

        self.conn.commit()
        cursor.close()