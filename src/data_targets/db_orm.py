from sqlalchemy import (
    Column,
    String,
    Integer,
    Time,
    Date,
    DateTime,
    Float,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class DimCoin(Base):
    __tablename__ = "dim_coin_t"
    uuid = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    symbol = Column(String(2083))
    icon_url = Column(String(2083))

    coin_prices = relationship("FtCoinPrice", backref="coin")


class DimTime(Base):
    __tablename__ = "dim_time_t"
    time_id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Time, nullable=False)
    hour = Column(Integer, nullable=False)
    minute = Column(Integer, nullable=False)
    second = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("hour < 24 AND hour >= 0", name="hour_check"),
        CheckConstraint("minute < 60 AND minute >= 0", name="minute_check"),
        CheckConstraint("second < 60 AND second >= 0", name="second_check"),
    )

    coin_prices = relationship("FtCoinPrice", backref="time")
    stock_prices = relationship("FtStockPrice", backref="time")


class DimDate(Base):
    __tablename__ = "dim_date_t"
    date_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    day = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("day <= 31 AND day >= 0", name="day_check"),
        CheckConstraint("week <= 52 AND week >= 0", name="week_check"),
        CheckConstraint("month <= 12 AND month >= 0", name="month_check"),
        CheckConstraint("quarter <= 4 AND quarter >= 0", name="quarter_check"),
        CheckConstraint("year >= 0", name="year_check"),
    )

    coin_prices = relationship("FtCoinPrice", backref="date")
    stock_prices = relationship("FtStockPrice", backref="date")


class FtCoinPrice(Base):
    __tablename__ = "ft_coin_price_t"
    uuid = Column(String(255), ForeignKey("dim_coin_t.uuid"), primary_key=True)
    time_id = Column(Integer, ForeignKey("dim_time_t.time_id"), primary_key=True)
    date_id = Column(Integer, ForeignKey("dim_date_t.date_id"), primary_key=True)
    price = Column(Float, nullable=False)
    change = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)


class Predictions(Base):
    __tablename__ = "predictions_t"
    entity = Column(String(255), primary_key=True)
    datetime = Column(DateTime, primary_key=True)
    predicted_values = Column(Float)


class DimStock(Base):
    __tablename__ = "dim_stock_t"
    symbol = Column(String(255), primary_key=True)
    company_name = Column(String(255))
    icon_url = Column(String(2083))
    exchange = Column(String(255))
    industry = Column(String(255))

    stock_prices = relationship("FtStockPrice", backref="stock")


class FtStockPrice(Base):
    __tablename__ = "ft_stock_price_t"
    symbol = Column(String(255), ForeignKey("dim_stock_t.symbol"), primary_key=True)
    time_id = Column(Integer, ForeignKey("dim_time_t.time_id"), primary_key=True)
    date_id = Column(Integer, ForeignKey("dim_date_t.date_id"), primary_key=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
