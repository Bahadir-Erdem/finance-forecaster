import psycopg2
import pyodbc
from sqlalchemy import create_engine
import time
import logging

class Database:
    def __init__(self, driver, server, database, user, password):
        self.driver = driver
        self.server = server
        self.database = database
        self.user = user
        self.password = password
        self.conn_str = f"{self.driver};Server={self.server},1433;Database={self.database};Uid={self.user};Pwd={self.password};Encrypt=yes;TrustServerCertificate=yes;"
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

    def close(self):
        self.conn.close()
        self.engine.dispose()
        return self

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

        if exception_type:
            print(f"{exception_type}: {exception_value}")
            return False
        else:
            return True