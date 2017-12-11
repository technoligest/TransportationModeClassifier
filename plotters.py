#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
"""
Specialized plotter to plot all the points of the dataset.
"""
class Plotter:
  def __init__(self,df):
    self._df=df
  def _plotHistogramClass(self, df):
    fig, axes = plt.subplots(nrows=5, ncols=4, figsize=(20, 20), sharey=True)
    fig.suptitle(df.transportation_mode.iloc[0])
    k = 0
    for i in range(5):
      for j in range(4):
        axes[i,j].hist(np.array(df[df.columns[k]]))
        axes[i,j].set_title(df.columns[k])
        k += 1
    print("Finished plotting a subplot.")

  def plotHistogramPerClassAndFeature(self):
    print(self._df.transportation_mode.unique())
    for cl in self._df.transportation_mode.unique():
      self._plotHistogramClass(self._df[self._df.transportation_mode==cl])
    print("Done plotting.")
  def show(self):
    plt.show()
    print("Done showing.")



