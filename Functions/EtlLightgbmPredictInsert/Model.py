import pandas as pd
from sklearn.model_selection import train_test_split
import lightgbm as lgb

class Model:
    def get_future_dates(self, df_containing_dates):
        NUM_OF_DAYS_TO_PREDICT = 14
        temp = pd.DataFrame()
        temp['date'] = pd.to_datetime(df_containing_dates[['year', 'month', 'day']])  # eklenebilir  'hour', 'minute
        newest_date = temp['date'].max() + pd.DateOffset(days=1)
        new_dates = pd.date_range(newest_date, periods=NUM_OF_DAYS_TO_PREDICT, freq='D').to_pydatetime()

        # minute_dates = pd.date_range(newest_date, periods=24*60, freq='T').to_pydatetime()
        # hour_dates = pd.date_range(newest_date, periods=24, freq='H').to_pydatetime()

        all_dates = list(new_dates)  # + list(minute_dates) + list(hour_dates)
        df = pd.DataFrame(all_dates)

        year = df[0].dt.year
        month = df[0].dt.month
        day = df[0].dt.day
        # hour = df[0].dt.hour
        # minute = df[0].dt.minute

        future_dates = pd.DataFrame({
            'year': year,
            'month': month,
            'day': day,
            # 'hour': hour,
            # 'minute': minute,
        })

        return future_dates

    def lightgbm(self, dataset):
        X = dataset.drop(columns=['price'])
        y = dataset.loc[:, 'price']
        TRAIN_SIZE = 0.8

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=TRAIN_SIZE, random_state=42)

        params = {
            'objective': 'regression',
            'metric': 'rmse',
        }

        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val)

        model = lgb.train(params, train_data, valid_sets=[train_data, val_data], num_boost_round=1000)
        future_dates = self.get_future_dates(X)

        predictions = model.predict(future_dates)

        y_val_pred = model.predict(X_val)
        # val_rmse = mean_squared_error(y_val, y_val_pred, squared=False)

        return predictions, future_dates
    