import pyodbc
from sqlalchemy import create_engine
import logging
import time

class Database:
    def __init__(self, driver, server, database, username, password):
        self.driver = driver
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.conn_str = f'{self.driver};Server={self.server},1433;Database={self.database};Uid={self.username};Pwd={self.password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=300;'
        self.max_retry_attempts = 3
        self.retry_delay = 30  # seconds

    def connect(self):
        retry_count = 0
        last_error = None

        while retry_count < self.max_retry_attempts:
            try:
                self.conn = pyodbc.connect(self.conn_str)
                self.engine = create_engine('mssql+pyodbc://', creator=lambda: self.conn)
                return self
            
            except pyodbc.Error as error:
                retry_count += 1
                time.sleep(self.retry_delay)

        if last_error is not None:
            logging.error(f"Failed to establish a database connection after multiple retries. Error: {last_error}")
            return None
    
        return self

    # def connect_to_local_postgres(self):
    #     retry_count = 0
    #     last_error = None

    #     while retry_count < self.max_retry_attempts:
    #         try:
    #             conn = psycopg2.connect(host=self.server, database=self.database, user=self.username, password=self.password)
    #             connection_string = f'postgresql://{self.username}:{self.password}@{self.server}/{self.database}'
    #             engine = create_engine(connection_string, creator=lambda: conn)
    #             return self
            
    #         except psycopg2.Error as error:
    #             retry_count += 1
    #             time.sleep(self.retry_delay)

    #     if last_error is not None:
    #         logging.error(f"Failed to establish a database connection after multiple retries. Error: {last_error}")
    #         return None
    
    #     return self

    def close(self):
        self.conn.close()
        return self

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if exception_type:
            logging.error(f'{exception_type}: {exception_value}')
            self.close()
            return False
        else:
            return self.close()