# coding: utf-8

# ## TODO
# - Calculate bearing properly

# In[36]:


import pandas as pd
import datetime as dt
import numpy as np
from geopy.distance import vincenty
import statistics as st

pd.set_option('display.width', 1000)
get_ipython().magic('matplotlib inline')
print("Done.")

# In[5]:


raw_geo = pd.read_csv("/Users/yaseralkayale/Documents/classes/current/csci6516 Big Data/Project/geolife_raw.csv",
                      sep='[\s,]',
                      header=None,
                      engine='python',
                      skiprows=1,
                      names=['user_id', 'date', 'time', 'latitude', 'longitude', 'transportation_mode'],
                      converters={
                        'date': lambda x: dt.datetime.strptime(x, '%Y-%m-%d'),
                        'time': lambda x: dt.datetime.strptime(x[0:-3], '%H:%M:%S')
                      }
                      # ,nrows = 500000
                      )
print("Done.")

# In[37]:


raw_geo = raw_geo.sort_values(['time'])
geo = raw_geo[raw_geo.transportation_mode != 'motorcycle']
geo = geo[geo.transportation_mode != 'run']
subtrajectories = geo.groupby(['user_id', 'date']).filter(lambda x: len(x) > 9).groupby(['user_id', 'date'])

print("Done.")

# In[ ]:



"""
This is mainly to make my life easier
"""
measure_vals = ['distance', 'speed', 'acceleration', 'bearing']
print("started")
def calcBearing(a, b):
  lat1, lon1, lat2, lon2 = a, b
  dLon = lon2 - lon1
  y = sin(dLon) * cos(lat2)
  x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
  return atan2(y, x)

def split_group(positions):
  print("Got into split group.")
  curr_point = positions.iloc[0]
  result = []

  curr_group = pd.DataFrame(columns=[positions.columns])
  curr_group.append(curr_point)
  for p in range(1, len(positions)):
    if positions.iloc[p]['transportation_mode'] == curr_point['transportation_mode']:
      curr_group.append(positions.iloc[p])
    else:
      result.append(curr_group)
      curr_point = positions.iloc[p]
      curr_group = pd.DataFrame(columns=[positions.columns])
      curr_group.append(curr_point)
  return result

"""
Group contains points of the same transportation mode.
"""
def calc_group_stats(group):
  print("Got into group stats")
  measures = {
    'distance': [0],
    'speed': [0],
    'acceleration': [0],
    'bearing': [0]
  }
  print("group: ", group)
  for i in range(1, len(group.index)):
    distance = vincenty(tuple(positions.iloc[i - 1][['latitude', 'longitude']]),
                        tuple(positions.iloc[i][['latitude', 'longitude']])).meters
    time = (positions.iloc[i]['time'].to_pydatetime() -
            positions.iloc[i - 1]['time'].to_pydatetime()).total_seconds()
    speed = distance / time
    acceleration = (speed - measures['speed'][i - 1]) / time
    bearing = calcBearing(tuple(positions.iloc[i - 1][['latitude', 'longitude']]),
                          tuple(positions.iloc[i][['latitude', 'longitude']]))
    measures['distance'].append(distance)
    measures['speed'].append(speed)
    measuers['acceleration'].append(acceleration)
    measures['bearing'].append(bearing)
  calcs = {
    'min': lambda x: min(x),
    'max': lambda x: max(x),
    'mean': lambda x: st.mean(x),
    'median': lambda x: st.median(x),
    'sd': lambda x: st.stdev(x)
  }
  result = {
    'distance': { 'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'sd': 0 },
    'speed': { 'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'sd': 0 },
    'acceleration': { 'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'sd': 0 },
    'bearing': { 'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'sd': 0 }
  }
  for m in measures:
    print(measures[m])
  # for m in measures:
  #     for stat in calcs:
  #       result[m][stat] = calcs[stat](measures[m])
  return result

def find_stats(subtrajectory):
  print("Got into find_stats")
  return [calc_group_stats(group) for group in split_group(subtrajectory)]

result = [find_stats(j) for i, j in subtrajectories]

print("Done.")



# ## References
# - https://code.activestate.com/recipes/577594-gps-distance-and-bearing-between-two-gps-points/ Retrieved calc_bearing code on Dec 3, 2017
#
