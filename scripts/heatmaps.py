# %%
import matplotlib as mpl
import matplotlib.pyplot as plt
import polyptich as pp
import pandas as pd
import numpy as np
pp.setup_ipython()

# %%
data = pd.DataFrame(np.random.randn(1000, 20))
obs = pd.DataFrame({
    "celltype":["Kupffer cells"] * 300 + ["Stellate cells"] * 300 + ["Stupid cells"] * 400
})
celltypes = pd.DataFrame.from_dict({
    "Kupffer cells": {"color": "red"},
    "Stellate cells": {"color": "blue"},
    "Stupid cells": {"color": "green"}
}, orient = "index")
var = pd.DataFrame(index = [f"gene_{i}" for i in range(20)])
var["module"] = ["Module 1"] * 5 + ["Module 2"] * 5 + ["Module 3"] * 10
var["color"] = np.random.choice(["pink", "cyan", "yellow"], 20)
data.columns = var.index
modules = pd.DataFrame({
    "module":["Module 1", "Module 2", "Module 3"],
    "color":["red", "blue", "green"]
}).set_index("module")

# %%
fig = pp.Figure(pp.Grid(padding_height = 0., padding_width = 0.))

row_layout = pp.heatmap.layouts.Broken(var["module"].astype("category"), padding = 0.)
col_layout = pp.heatmap.layouts.Broken(obs["celltype"].astype("category"), padding = 0.1)

norm = mpl.colors.Normalize()
main_heatmap = fig.main.add(pp.heatmap.Heatmap(data, row_layout = row_layout, col_layout = col_layout, norm = norm, cmap = "magma"))

heading = fig.main.add_above(pp.heatmap.heading.HeadingTop(obs, celltypes, col_layout))

ticks = fig.main.add_left(pp.heatmap.ticks.TicksLeft(var, row_layout), row = main_heatmap)
heading = fig.main.add_left(pp.heatmap.heading.HeadingLeft(var, modules, row_layout), row = main_heatmap)
fig.display()


# %%
