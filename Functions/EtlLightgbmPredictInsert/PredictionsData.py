from .Database import Database
from .Model import Model
from .TrainingData import TrainingData
import pandas as pd

class PredictionsData:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.conn = database.conn
        self.engine = database.engine
        self.model = Model()
        self.training_data = TrainingData()

    def predict_and_to_db(self):
        self.results = []

        training_df = self.training_data.get_training_data()

        for entity in training_df['entity'].unique():
            train_dataset = training_df.loc[training_df['entity'] == entity, training_df.columns != 'entity']
            predictions, result = self.model.lightgbm(train_dataset)
            result['predicted_values'] = predictions
            result['entity'] = entity
            result['date'] = pd.to_datetime(result[['year', 'month', 'day']])
            result.drop(columns=['year', 'month', 'day'], inplace=True)
            self.results.append(result)

        results_df = pd.concat(self.results)
        results_df.to_sql('predictions_t', self.engine, if_exists='replace', index=False)