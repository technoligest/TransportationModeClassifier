#!/usr/bin/python3
from classifier import *
from data_preprocessor import *
from plotters import *

import scipy as sp

pd.set_option('display.width', 1000)

# Preprocess the data so that we can use it
def process_data(nrows=None, outpufFileName = "result.csv"):
  df = read_data("/Users/yaseralkayale/Documents/classes/current/csci6516 Big Data/Project/geolife_raw.csv", nrows)
  print("Done reading in.")
  result = computeData(df)
  print("Done the computations")
  result.to_csv(outpufFileName)
  print("Done saving result file.")

# Plot the datapoints
def plot_graph(filename):
  df = pd.read_csv(filename, usecols=range(1, 22))
  p = Plotter(df)
  p.plotHistogramPerClassAndFeature()
  p.show()



def runTTest(df, algo):
  validator = Validator(df)
  statistic, p_val = sp.stats.ttest_ind(validator.cross_validate_flat(k=10, algo=algo),
                                        validator.cross_validate_heirarchal(k=10, algo=algo),
                                        equal_var=True)
  print("Statistic = ", statistic," p-val= ", p_val)



# plot_graph("result2.csv")
# run_everything(nrows = None, outpufFileName="result2.csv")
df = pd.read_csv("/Users/yaseralkayale/Documents/classes/current/csci6516 Big Data/Project/result2.csv", usecols=range(1, 22))
runTTest(df, None)
