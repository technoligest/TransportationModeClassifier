#!/usr/bin/python3
import pandas as pd
import datetime as dt
import math
import numpy as np
import pandas as pd
from utils import *


# from values_calculator import ValueCalculator


class ValueCalculator:
  def __init__(self, df):
    self._df = df
  def _calculate_initial_compass_bearing(self, pointA, pointB):
    if (type(pointA) != tuple) or (type(pointB) != tuple):
      raise TypeError("Only tuples are supported as arguments")
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

  def _haversine_distance(self, origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c
    return d

  def _get_masks(self):
    ids_list = np.array(self._df.id)
    return [0 if i == (len(ids_list) - 1) or ids_list[i] != ids_list[i + 1] else 1 for i in range(len(ids_list))]

  def _add_timediff(self):
    timediff = [(self._df.time.iloc[i + 1] - self._df.time.iloc[i]).total_seconds()
                if i != (len(self._df.time) - 1)
                else 0
                for i in range(len(self._df.time))]
    timediff = [timediff[i] * self._mask[i] for i in range(len(timediff))]
    self._df['timediff'] = timediff

  def _add_distance(self):
    distance = [self._haversine_distance((self._df.lat.iloc[i], self._df.lon.iloc[i]),
                                         (self._df.lat.iloc[i + 1], self._df.lon.iloc[i + 1]))
                if i != (len(self._df.time) - 1)
                else 0
                for i in range(len(self._df.time))]
    distance = [distance[i] * self._mask[i] for i in range(len(distance))]
    self._df['distance'] = distance

  def _add_speed(self):
    speed = [self._df.distance.iloc[i] / (self._df.timediff.iloc[i] + 0.1 ** 10) for i in range(len(self._df.time))]
    speed = [speed[i] * self._mask[i] for i in range(len(speed))]
    self._df['speed'] = speed

  def _add_acc(self):
    acc = [(self._df.speed.iloc[i + 1] - self._df.speed.iloc[i]) / (self._df.timediff.iloc[i] + 0.1 ** 10)
                if i != (len(self._df.time) - 1)
                else 0
                for i in range(len(self._df.time))]
    acc = [acc[i] * self._mask[i] for i in range(len(acc))]
    self._df['acc'] = acc

  def _add_bearing(self):
    bearing = [self._calculate_initial_compass_bearing((self._df.lat.iloc[i], self._df.lon.iloc[i]),
                                                       (self._df.lat.iloc[i + 1], self._df.lon.iloc[i + 1]))
               if i != (len(self._df.time) - 1) else 0 for i in range(len(self._df.time))]
    bearing = [bearing[i] * self._mask[i] for i in range(len(bearing))]
    self._df['bearing'] = bearing

  def calc_vals(self):
    if (len(self._df.index) < 2):
      print("WHAT")
      return None
    self._mask = self._get_masks()
    self._add_timediff()
    self._add_distance()
    self._add_speed()
    self._add_acc()
    self._add_bearing()
    self._df = self._df[:-1]
    slice = self._df[['distance', 'speed', 'acc', 'bearing']]
    transport = pd.Series([self._df.transportation_mode.iloc[0]], ['transportation_mode'])
    result = pd.DataFrame()
    result = pd.concat([result, slice.mean(), slice.max(), slice.min(), slice.median(), slice.std(), transport], axis=0).T
    result.columns = ['distance_mean',   'speed_mean',   'acc_mean',   'bearing_mean',
                      'distance_max',    'speed_max',    'acc_max',    'bearing_max',
                      'distance_min',    'speed_min',    'acc_min',    'bearing_min',
                      'distance_mediam', 'speed_mediam', 'acc_median', 'bearing_mediam',
                      'distance_std',    'speed_std',    'acc_std',    'bearing_std',
                      'transportation_mode']
    return result
def read_data(file, nrows=None):
  raw_geo = pd.read_csv(file,
                    sep='[\s,]',
                    header=None,
                    engine='python',
                    skiprows=1,
                    names = ['id','date','time','lat','lon','transportation_mode'],
                    converters={
                      'date': lambda x: dt.datetime.strptime(x,'%Y-%m-%d'),
                      'time': lambda x: dt.datetime.strptime(x[0:-3],'%H:%M:%S')
                    }
                    , nrows = nrows
                    )
  raw_geo = raw_geo.sort_values(['time'])
  raw_geo = raw_geo[raw_geo.transportation_mode != 'motorcycle']
  raw_geo = raw_geo[raw_geo.transportation_mode != 'run']
  return raw_geo



def computeData(raw_geo):
  groups = raw_geo.groupby(['id', 'date'])
  result = pd.DataFrame()
  numTraj = 0
  for _, group in groups:
    group['diff'] = group.transportation_mode.ne(group.transportation_mode.shift()).cumsum()
    numTraj += len(group.groupby(['diff']).filter(lambda x: len(x) > 9).groupby(['diff']))
  i = 1
  for _, group in groups:
    group['diff'] = group.transportation_mode.ne(group.transportation_mode.shift()).cumsum()
    trajectories = group.groupby(['diff']).filter(lambda x: len(x) > 9).groupby(['diff'])
    for _, trajectory in trajectories:
      print("\tStarting trajectory ", i, "/", numTraj)
      i += 1
      result = result.append(ValueCalculator(trajectory).calc_vals())
  return result

