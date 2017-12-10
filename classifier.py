import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier as rfc
from sklearn.model_selection import cross_val_score as cvc


class Classify:
  def __init__(self, df, predictor=None):
    self._df = df
    self._flat_model = None
    self._heirarchy_models = None
    if predictor == None:
      self._predictor = rfc()
    else:
      self._predictor = predictor

  def fit(self):
    self._fitFlatModel()
    self._fitHeirarchyModel()

  def _fitFlatModel(self):
    print(len(self._df.drop(['transportation_mode'], axis=1)))
    self._flat_model = self._predictor.fit(self._df.drop(['transportation_mode'], axis=1), self._df.transportation_mode)

  def _fitHeirarchyModel(self):
    topLayer = self._df.copy()
    topLayer.loc[topLayer.transportation_mode == 'taxi', 'transportation_mode'] = 'vehicle'
    topLayer.loc[topLayer.transportation_mode == 'car', 'transportation_mode'] = 'vehicle'
    topLayer.loc[topLayer.transportation_mode == 'bus', 'transportation_mode'] = 'vehicle'

    topLayer.loc[topLayer.transportation_mode == 'train', 'transportation_mode'] = 'train/subway'
    topLayer.loc[topLayer.transportation_mode == 'subway', 'transportation_mode'] = 'train/subway'
    topLayer_model = self._predictor.fit(topLayer.drop(['transportation_mode'], axis=1), topLayer.transportation_mode)

    train_subway_layer = self._df[
      (self._df.transportation_mode == 'train') | (self._df.transportation_mode == 'subway')]
    train_subway_layer_model = self._predictor.fit(
      train_subway_layer.drop(['transportation_mode'], axis=1), train_subway_layer.transportation_mode)

    vehicle_layer = self._df[(self._df.transportation_mode == 'car') |
                             (self._df.transportation_mode == 'bus') |
                             (self._df.transportation_mode == 'taxi')]

    vehicle_layer_model = self._predictor.fit(vehicle_layer.drop(['transportation_mode'], axis=1),
                                              vehicle_layer.transportation_mode)

    self._heirarchy_models = { "vehicle": vehicle_layer_model, "top": topLayer_model,
                               "train/subway": train_subway_layer_model }

  def heirarchy_predict(self, values):
    assert (self._heirarchy_models != 'heireirchy')
    topLayer_prediction = self._heirarchy_models['top'].predict(values)

    train_subway_pos = np.where(topLayer_prediction == 'train/subway')
    train_subway_prediction = self._heirarchy_models['train/subway'].predict(values.iloc[train_subway_pos])
    topLayer_prediction[train_subway_pos] = train_subway_prediction

    vehicle_pos = np.where(topLayer_prediction == 'vehicle')
    vehicle_prediction = self._heirarchy_models['vehicle'].predict(values.iloc[vehicle_pos])
    topLayer_prediction[vehicle_pos] = vehicle_prediction
    return topLayer_prediction

  def flat_predict(self, values):
    assert (self._flat_model != None)
    return self._flat_model.predict(values)

  def predict(self, values):
    assert (self.Fitted), "The classifier has not been fitted yet."
    if self.model == "flat":
      return self._flat_model.predict(values)
    elif self.model == "heireirchy":
      return self._heirarchy_predict(values)
    assert (False), "Something is wrong with the code implementation. Contact the dumb coder."

df = pd.read_csv("result2.csv", usecols=range(1, 22))
cl = Classify(df).fitHeirarchyModel()
