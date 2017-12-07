import pandas as pd
import datetime as dt
from values_calculator import *

pd.set_option('display.width', 1000)

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
                      # , nrows = 500000
                      )
print("Done reading in.")


raw_geo         = raw_geo.sort_values(['time'])
raw_geo         = raw_geo[raw_geo.transportation_mode != 'motorcycle']
raw_geo         = raw_geo[raw_geo.transportation_mode != 'run']


groups = raw_geo.groupby(['id','date'])
result = pd.DataFrame()


i = 1
l = len(groups)
for _, group in groups:
  print("Starting group ",i,"/",l)
  i+=1
  group['diff'] = group.transportation_mode.ne(group.transportation_mode.shift()).cumsum()
  trajectories = group.groupby(['diff'])
  l2 = len(trajectories)
  i2=1
  for _, trajectory in trajectories:
    print("\tStarting trajectory ", i2, "/", l2)
    i2+=1
    result = result.append(ValueCalculator(trajectory).calc_vals())

result.to_csv("Result.csv")

print("Done everything.")

