from abc import ABC, abstractmethod
from time import sleep

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, session, DeclarativeBase
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import SQLAlchemyError
from .db_orm import (
    DimDate,
    DimStock,
    DimTime,
    DimCoin,
    FtCoinPrice,
    FtStockPrice,
    Predictions,
    Base,
)
from src.transformations.transformations import Transformer


class DataTarget(ABC):
    @abstractmethod
    def save(self, data: Transformer):
        pass


class Database(DataTarget):
    def __init__(self, connection_string: str, max_retries=3, delay=30) -> None:
        self.connection_string = connection_string
        self.engine = None
        self.Session = None
        self.max_retries = max_retries
        self.delay = delay
        self._initialize_with_retry()
        super().__init__()

    def _initialize_with_retry(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.engine = create_engine(self.connection_string)
                self.Session = sessionmaker(bind=self.engine)
                Base.metadata.create_all(self.engine)
                return
            except SQLAlchemyError as e:
                retries += 1
                if retries == self.max_retries:
                    raise Exception(
                        (
                            f"Failed to initialize database after {self.max_retries} attempts: {str(e)}",
                            f"Attempt {retries} failed. Retrying in {self.delay} seconds...",
                        )
                    )

                sleep(self.delay)

    def save(self, transformer: Transformer):
        with self.Session() as session:
            session.begin()
            try:
                data = transformer.transform()
                self._save_data(session, data)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise SQLAlchemyError(f"Failed to save data: {e}")
            except Exception as e:
                raise Exception(f"Error happened: {e}")

    def _save_data(self, session: session, data: pd.DataFrame):
        raise NotImplementedError("This method must be implemented by subclasses")

    def truncate_table(self, table_object: DeclarativeBase):
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text(f"TRUNCATE TABLE {table_object.__tablename__}"))
                transaction.commit()
            except:
                transaction.rollback()
                raise

    def get_or_create(self, session: session, model, **kwargs):
        try:
            instance = session.query(model).filter_by(**kwargs).one()
            return instance, False
        except NoResultFound:
            instance = model(**kwargs)
            session.add(instance)
            session.flush()
            session.refresh(instance)
            return instance, True

    def get_model_column_names(
        self, model: DeclarativeBase, only_primary_keys=False, exclude_primary_key=True
    ) -> list:
        all_columns = [col.key for col in model.__table__.columns]

        if only_primary_keys:
            mapper = inspect(model).mapper
            return [col.name for col in mapper.primary_key]
        elif exclude_primary_key:
            mapper = inspect(model).mapper
            primary_key_columns = [col.name for col in mapper.primary_key]
            return [col for col in all_columns if col not in primary_key_columns]
        else:
            return all_columns

    def does_row_exist(self, session: session, model: DeclarativeBase):
        try:
            columns = self.get_model_column_names(model, only_primary_keys=True)
            values = {column: getattr(model, column) for column in columns}
            session.query(model.__class__).filter_by(**values).one()
            return True
        except NoResultFound:
            return False


class DBCoinTarget(Database):
    def _save_data(self, session: session, data: pd.DataFrame):
        for _, row in data.iterrows():
            date, _ = self.get_or_create(
                session, DimDate, **row[self.get_model_column_names(DimDate)]
            )
            time, _ = self.get_or_create(
                session, DimTime, **row[self.get_model_column_names(DimTime)]
            )
            coin, _ = self.get_or_create(
                session,
                DimCoin,
                **row[self.get_model_column_names(DimCoin, exclude_primary_key=False)],
            )
            price = row["price"]
            change = row["change"]
            rank = row["rank"]
            coin_price = FtCoinPrice(
                uuid=coin.uuid,
                time_id=time.time_id,
                date_id=date.date_id,
                price=price,
                change=change,
                rank=rank,
            )
            if not self.does_row_exist(session, coin_price):
                session.add(coin_price)


class DBStockTarget(Database):
    def _save_data(self, session: session, data: pd.DataFrame):
        for _, row in data.iterrows():
            date, _ = self.get_or_create(
                session, DimDate, **row[self.get_model_column_names(DimDate)]
            )
            time, _ = self.get_or_create(
                session, DimTime, **row[self.get_model_column_names(DimTime)]
            )
            stock, _ = self.get_or_create(
                session,
                DimStock,
                **row[self.get_model_column_names(DimStock, exclude_primary_key=False)],
            )
            open = row["open"]
            high = row["high"]
            low = row["low"]
            close = row["close"]
            stock_price = FtStockPrice(
                symbol=stock.symbol,
                time_id=time.time_id,
                date_id=date.date_id,
                open=open,
                high=high,
                low=low,
                close=close,
            )
            if not self.does_row_exist(session, stock_price):
                session.add(stock_price)


class DBPredictionTarget(Database):
    def _save_data(self, session: session, data: pd.DataFrame):
        self.truncate_table(Predictions)

        for _, row in data.iterrows():
            prediction = Predictions(**row)
            session.add(prediction)
