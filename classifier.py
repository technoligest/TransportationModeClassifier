#!/usr/bin/python3
"""
This class helps us classify and predict the classes using a flat classifier or using a heirarchical approach.
"""

import numpy as np
from sklearn.tree import DecisionTreeClassifier as rfc
from sklearn.model_selection import StratifiedKFold as skf
from sklearn import metrics as met


class Classifier:
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
    self._flat_model = self._predictor.fit(self._df.drop(['transportation_mode'], axis=1), self._df.transportation_mode)

  def _fitHeirarchyModel(self):
    topLayer = self._df.copy()
    topLayer.loc[topLayer.transportation_mode == 'taxi', 'transportation_mode'] = 'vehicle'
    topLayer.loc[topLayer.transportation_mode == 'car', 'transportation_mode'] = 'vehicle'
    topLayer.loc[topLayer.transportation_mode == 'bus', 'transportation_mode'] = 'vehicle'

    topLayer.loc[topLayer.transportation_mode == 'train', 'transportation_mode'] = 'train/subway'
    topLayer.loc[topLayer.transportation_mode == 'subway', 'transportation_mode'] = 'train/subway'
    topLayer_model = self._predictor.fit(topLayer.drop(['transportation_mode'], axis=1), topLayer.transportation_mode)

    # print(topLayer.transportation_mode.unique())
    # print()
    train_subway_layer = self._df[(self._df.transportation_mode == 'train') |
                                  (self._df.transportation_mode == 'subway')]

    # print(train_subway_layer.transportation_mode.unique())
    # print()
    if len(train_subway_layer.index)>0:
      train_subway_layer_model = self._predictor.fit(train_subway_layer.drop(['transportation_mode'], axis=1),
                                                     train_subway_layer.transportation_mode)
    else:
      train_subway_layer_model = None

    vehicle_layer = self._df[(self._df.transportation_mode == 'car') |
                             (self._df.transportation_mode == 'bus') |
                             (self._df.transportation_mode == 'taxi')]
    # print(vehicle_layer.transportation_mode.unique())
    # print()
    if len(vehicle_layer.index)>0:
      vehicle_layer_model = self._predictor.fit(vehicle_layer.drop(['transportation_mode'], axis=1),
                                              vehicle_layer.transportation_mode)
    else:
      vehicle_layer_model = None

    self._heirarchy_models = { "vehicle": vehicle_layer_model, "top": topLayer_model,
                               "train/subway": train_subway_layer_model }

  def heirarchy_predict(self, values):
    assert (self._heirarchy_models != 'heireirchy')
    topLayer_prediction = self._heirarchy_models['train/subway'].predict(values)
    print("Tope layer predictions:")
    print(np.unique(topLayer_prediction))
    print()
    assert( self._heirarchy_models['train/subway'] != None), "There should be a train/subway model, but was not found."
    train_subway_pos = np.where(topLayer_prediction == 'train/subway')
    if len(train_subway_pos)>0:
      train_subway_prediction = self._heirarchy_models['train/subway'].predict(values.iloc[train_subway_pos])
      topLayer_prediction[train_subway_pos] = train_subway_prediction
    assert(self._heirarchy_models['vehicle']!=None) , "There should be a vehicle model, but was not found."
    vehicle_pos = np.where(topLayer_prediction == 'vehicle')
    if len(vehicle_pos)>0:
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

class Validator:
  def __init__(self, df):
    self._df = df

  def cross_validate_flat(self, k=10, algo=rfc()):
    SKF = skf(k)
    accuracy = np.array([])
    for train, test in SKF.split(self._df.drop(['transportation_mode'], axis=1), self._df.transportation_mode):
      c = Classifier(self._df.iloc[train], algo)
      c.fit()
      prediction = c.flat_predict(self._df.iloc[test].drop(['transportation_mode'], axis=1))
      actual = np.array(self._df.iloc[test].transportation_mode)
      np.append(accuracy, met.accuracy_score(prediction, actual))
    return accuracy

  def cross_validate_heirarchal(self, k=10, algo=rfc()):
    SKF = skf(k)
    accuracy = []
    for train, test in SKF.split(self._df.drop(['transportation_mode'], axis=1), self._df.transportation_mode):
      c = Classifier(self._df.iloc[train], algo)
      c.fit()
      prediction = c.heirarchy_predict(self._df.iloc[test].drop(['transportation_mode'], axis=1))
      accuracy.extend(met.accuracy_score(prediction, self._df.iloc[test].transportation_mode))
    return accuracy







