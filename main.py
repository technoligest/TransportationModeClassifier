import pandas as pd
import datetime as dt
from values_calculator import *

pd.set_option('display.width', 1000)


def read_data(file, nrows=None):
  return pd.read_csv(file,
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


def clean_data(raw_geo):
  raw_geo         = raw_geo.sort_values(['time'])
  raw_geo         = raw_geo[raw_geo.transportation_mode != 'motorcycle']
  raw_geo         = raw_geo[raw_geo.transportation_mode != 'run']
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

def run_everything():
  df = read_data("/Users/yaseralkayale/Documents/classes/current/csci6516 Big Data/Project/geolife_raw.csv")
  print("Done reading in.")
  df = clean_data(df)
  print("Done data cleaning.")
  result = computeData(df)
  print("Done the computations")
  result.to_csv("Result.csv")
  print("Done everything.")

run_everything()


