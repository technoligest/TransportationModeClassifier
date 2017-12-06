

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
                      # ,nrows = 50000
                      )
print("Done.")


# In[ ]:


class ValueCalculator:

  """
  Copied from https://gist.github.com/jeromer/2005586
  """
  def _calculate_initial_compass_bearing(self,pointA, pointB):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
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
  def calc_vals(self):
    self._mask = self._get_masks()
    self._add_timediff()
    self._add_distance()
    self._add_speed()
    self._add_acc()
    self._add_bearing()
    return self._df


raw_geo = raw_geo.sort_values(['time'])
geo = raw_geo[raw_geo.transportation_mode != 'motorcycle']
geo = geo[geo.transportation_mode != 'run']
subtrajectories = geo.groupby(['id','date']).filter(lambda x: len(x) > 9).groupby(['id','date'])

newGroups = [ValueCalculator(df).calc_vals() for _,df in subtrajectories]


print("Done.")





"""
This is mainly to make my life easier
"""
measure_vals = ['distance', 'speed', 'acceleration', 'bearing']
print("started")
def calcBearing(a,b):
    lat1, lon1,lat2, lon2 = a,b
    dLon = lon2 - lon1
    y = sin(dLon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
    return atan2(y, x)
  


"""
Group contains points of the same transportation mode.
"""
def calc_group_stats(group):
  print("Got into group stats")
  measures = {
    'distance'    : [0],
    'speed'       : [0],
    'acceleration': [0],
    'bearing'     : [0]
  }
  print("group: ",group)
  for i in range(1, len(group.index)):
    distance = vincenty(tuple(group.iloc[i-1][['latitude','longitude']]),
                        tuple(group.iloc[i][['latitude','longitude']])).meters
    time = (group.iloc[i]['time'].to_pydatetime()-
            group.iloc[i-1]['time'].to_pydatetime()).total_seconds()
    speed = distance/time
    acceleration = (speed - measures['speed'][i-1]) / time
    bearing = calcBearing(tuple(group.iloc[i-1][['latitude','longitude']]),
                          tuple(group.iloc[i][['latitude','longitude']]))
    measures['distance'].append(distance)
    measures['speed'].append(speed)
    measures['acceleration'].append(acceleration)
    measures['bearing'].append(bearing)
  calcs = {
    'min'   : lambda x: min(x),
    'max'   : lambda x: max(x),
    'mean'  : lambda x: st.mean(x),
    'median': lambda x: st.median(x),
    'sd'    : lambda x: st.stdev(x)
  } 
  result ={
    'distance'    : {'min':0, 'max':0,'mean':0,'median':0,'sd':0},
    'speed'       : {'min':0, 'max':0,'mean':0,'median':0,'sd':0},
    'acceleration': {'min':0, 'max':0,'mean':0,'median':0,'sd':0},
    'bearing'     : {'min':0, 'max':0,'mean':0,'median':0,'sd':0}
  }
  for m in measures:
    print(measures[m])
#   for m in measures:
#     for stat in calcs:
#       result[m][stat] = calcs[stat](measures[m])
  return result
  

  
def split_trajectory(positions):
  print("Got into split trajectory.")
  curr_point = positions.iloc[0]
  result = []
  
  curr_group = pd.DataFrame(columns=[positions.columns])
  curr_group = curr_group.append(curr_point,ignore_index=True)
  print(len(curr_group))
  for p in range(1,len(positions)):
    if positions.iloc[p]['transportation_mode'] == curr_point['transportation_mode']:
      curr_group =curr_group.append(positions.iloc[p],ignore_index=True)
    elif p == len(positions)-1:
      curr_group = curr_group.append(positions.iloc[p],ignore_index=True)
      result.append(curr_group)
    else:
      result.append(curr_group)
      curr_point = positions.iloc[p]
      curr_group = pd.DataFrame(columns=[positions.columns])
      curr_group = curr_group.append(curr_point,ignore_index=True)
  return result

def find_stats(subtrajectory):
  print("Got into find_stats")
#   return [calc_group_stats(group) for group in split_group(subtrajectory)]
  for group in split_trajectory(subtrajectory):
    print("The length: ",len(group))
  return None
# result =[find_stats(j) for i,j in subtrajectories]
for i,j in subtrajectories:
  print("Stats: ")
  print(find_stats(j))
  break
    
print("Done.")
    


# ## References
# - https://code.activestate.com/recipes/577594-gps-distance-and-bearing-between-two-gps-points/ Retrieved calc_bearing code on Dec 3, 2017
# 
