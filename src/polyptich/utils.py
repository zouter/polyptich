import numpy as np
import pandas as pd

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



def case_if(choices, default="other"):
    keys = list(choices.keys())
    values = list(choices.values())
    y = np.zeros(len(values[0]), dtype=int) + len(keys)
    for i, (key, value) in enumerate({k: v for k, v in zip(keys[::-1], values[::-1])}.items()):
        y[value] = i
    return np.array([*keys[::-1], default])[y]


def crossing(*dfs, **kwargs):
    dfs = [df.copy() if isinstance(df, pd.DataFrame) else df.to_frame() for df in dfs]
    if any(len(df) == 0 for df in dfs):
        return pd.DataFrame(columns = list(set().union(*(df.columns for df in dfs))))
    dfs.extend(pd.DataFrame({k: v}) for k, v in kwargs.items())
    for df in dfs:
        df["___key"] = 0
    if len(dfs) == 0:
        return pd.DataFrame()
    dfs = [df for df in dfs if df.shape[0] > 0]  # remove empty dfs
    base = dfs[0]
    for df in dfs[1:]:
        base = pd.merge(base, df, on="___key")
    return base.drop(columns=["___key"])
