import numpy as np


def case_when(default="other", **kwargs):
    y = np.zeros(len(kwargs[list(kwargs.keys())[0]]), dtype=int) + len(kwargs)
    for i, (key, value) in enumerate({k: kwargs[k] for k in list(kwargs.keys())[::-1]}.items()):
        y[value] = i
    return np.array([*kwargs.keys(), default])[y]
