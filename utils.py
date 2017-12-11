#!/usr/bin/python3
import time

"""
Print the running time of a given function
"""
def printRunningTime(func):
  def wrapper(*args):
    print("started: ",func.__name__)
    start = time.time()
    result = func(*args)
    print(func.__name__, " ran in: ", (time.time() - start))
    return result
  return wrapper