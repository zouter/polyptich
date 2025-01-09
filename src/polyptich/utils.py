import numpy as np


def case_when(default="other", **kwargs):
    y = np.zeros(len(kwargs[list(kwargs.keys())[0]]), dtype=int) + len(kwargs)
    for i, (key, value) in enumerate({k: kwargs[k] for k in list(kwargs.keys())[::-1]}.items()):
        y[value] = i
    return np.array([*list(kwargs.keys())[::-1], default])[y]


def case_switch(default="other", *args):
    keys = args[::2]
    values = args[1::2]
    y = np.zeros(len(keys[0]), dtype=int) + len(keys)
    for i, (key, value) in enumerate({k: v for k, v in zip(keys[::-1], values[::-1])}.items()):
        y[value] = i
    return np.array([*keys[::-1], default])[y]