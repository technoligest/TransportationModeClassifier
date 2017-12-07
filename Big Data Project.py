

import pandas as pd
import datetime as dt
import numpy as np
from geopy.distance import vincenty
import statistics as st
import gpxpy
import math
pd.set_option('display.width', 1000)
# get_ipython().magic('matplotlib inline')
print("Done.")


# In[ ]:


raw_geo = pd.read_csv("/Users/yaseralkayale/Documents/classes/current/csci6516 Big Data/Project/geolife_raw.csv",
                      sep='[\s,]',
                      header=None,
                      engine='python',
                      skiprows=1,
                      names = ['id','date','time','lat','lon','transportation_mode'],
                      converters={
                        'date': lambda x: dt.datetime.strptime(x,'%Y-%m-%d'),
                        'time': lambda x: dt.datetime.strptime(x[0:-3],'%H:%M:%S')
                      }
                      ,nrows = 50000
                      )
print("Done.")


# In[ ]:


class ValueCalculator:

  def _calculate_initial_compass_bearing(self,pointA, pointB):
    if (type(pointA) != tuple) or (type(pointB) != tuple):
      raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                                           * math.cos(lat2) * math.cos(diffLong))

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
  def __init__(self,df):
    self._df = df
  def _get_masks(self):
    ids = self._df.id.unique()
    ids_list = np.array(self._df.id)
    return [0 if i==(len(ids_list)-1) or ids_list[i]!=ids_list[i+1] else 1 for i in range(len(ids_list))]
  def _add_timediff(self):
    timediff = [(self._df.time.iloc[i+1]-self._df.time.iloc[i]).total_seconds() if i!=(len(self._df.time)-1) else 0 for i in range(len(self._df.time))]
    timediff = [timediff[i]*self._mask[i] for i in range(len(timediff))]
    self._df['timediff'] = timediff
  def _add_distance(self):
    distance = [self._haversine_distance((self._df.lat.iloc[i], self._df.lon.iloc[i]),(self._df.lat.iloc[i+1],self._df.lon.iloc[i+1]))
                if i!=(len(self._df.time)-1) else 0 for i in range(len(self._df.time))]
    distance = [distance[i]*self._mask[i] for i in range(len(distance))]
    self._df['distance']=distance
  def _add_speed(self):
    speed = [self._df.distance.iloc[i]/(self._df.timediff.iloc[i]+0.1**1000) for i in range(len(self._df.time))]
    speed = [speed[i]*self._mask[i] for i in range(len(speed))]
    self._df['speed'] = speed
  def _add_acc(self):
    acc = [(self._df.speed.iloc[i+1]-self._df.speed.iloc[i])/(self._df.timediff.iloc[i]+0.1**1000) if i!=(len(self._df.time)-1)
           else 0 for i in range(len(self._df.time))]
    acc = [acc[i]*self._mask[i] for i in range(len(acc))]
    self._df['acc'] = acc
  def _add_bearing(self):
    bearing = [self._calculate_initial_compass_bearing((self._df.lat.iloc[i],self._df.lon.iloc[i]),
                                                       (self._df.lat.iloc[i+1], self._df.lon.iloc[i+1]))
               if i!= (len(self._df.time)-1) else 0 for i in range(len(self._df.time))]
    bearing = [bearing[i]*self._mask[i] for i in range(len(bearing))]
    self._df['bearing'] = bearing

  def _split_df(self):
    temp_val = self._df.transportation_mode.iloc[0]
    temp_df = pd.DataFrame()
    temp_df = temp_df.append(self._df.iloc[0])
    dfs = []
    for i in range(1, len(self._df.id)):
      if self._df.transportation_mode.iloc[i] != temp_val or i == len(self._df.id) - 1:
        dfs.append(temp_df)
        print("Just appended df of size: ", temp_df.shape)
        temp_df = pd.DataFrame()
        temp_df = temp_df.append(self._df.iloc[i])
        temp_val = self._df.transportation_mode.iloc[i]
      else:
        temp_df = temp_df.append(self._df.iloc[i])
    print("finished splitting.")
    return dfs

  def calc_vals(self):
    df_backup = self._df
    result = pd.DataFrame()
    for df in self._split_df():
      print("Started iteration with _df shape: ", df.shape)
      self._df = df
      self._mask = self._get_masks()
      self._add_timediff()
      print("Finsihed timediff")
      self._add_distance()
      print("Finished distance")
      self._add_speed()
      print("Finsihed speed")
      self._add_acc()
      print("Finished acc")
      self._add_bearing()
      print("Finsihed bearing")
      slice = self._df[['distance','speed','acc','bearing']]
      means = slice.mean()
      means.columns = ['distance_mean','speed_mean','acc_mean', 'bearing_mean']
      print("Finished means.")
      amax = slice.max()
      amax.columns = [ 'distance_max','speed_max','acc_max', 'bearing_max']
      print("finished max.")
      amin = slice.min()
      amin.columns = ['distance_min','speed_min','acc_min', 'bearing_min']
      print("finished min.")
      amedian = slice.median()
      amedian.columns = [ 'distance_mediam','speed_mediam','acc_median', 'bearing_mediam']
      print("finished median")
      astd = slice.std()
      astd.columns = [ 'distance_std','speed_std','acc_std', 'bearing_std']
      tempResult = pd.DataFrame()
      print("finished std")

      transport = pd.Series( [df.transportation_mode.iloc[0]],['transportation_mode'])

      tempResult = pd.concat([tempResult, means, amax, amin, amedian, astd, transport],   axis=0)

      result     = result.append(tempResult.T)
      print("finished iteration.")
    result
    self._df = df_backup
    return result


raw_geo = raw_geo.sort_values(['time'])
geo = raw_geo[raw_geo.transportation_mode != 'motorcycle']
geo = geo[geo.transportation_mode != 'run']
subtrajectories = geo.groupby(['id','date']).filter(lambda x: len(x) > 9).groupby(['id','date'])

newGroups = [ValueCalculator(df).calc_vals() for _,df in subtrajectories]
result = pd.DataFrame()
for group in newGroups:
  print("Shape: ",group.shape)
for group in newGroups:
  print("columns: ", group.columns)
for group in newGroups:
  # print("Shape: ",group.shape)
  result = result.append(group)

print("Shape: ",result.shape)
print(result.columns)
print(result.index)
print("Done.")
