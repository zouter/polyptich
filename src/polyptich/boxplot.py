import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def grouped_boxplot(df, data_col, x_group_col, color_group_col, color_df, ax=None):
    """
    Creates a grouped boxplot with explicit control over x-axis grouping and color grouping.

    Args:
        df (pd.DataFrame): The main DataFrame containing the data.
        data_col (str): The name of the column with numerical data for the y-axis.
        x_group_col (str): The column for the primary grouping on the x-axis ticks.
        color_group_col (str): The column for subgrouping, represented by color.
        color_df (pd.DataFrame): A DataFrame where the index contains the names from
                                 the `color_group_col` and a 'color' column contains
                                 the desired colors.
        ax (matplotlib.axes.Axes, optional): The axes object to plot on. If None,
                                             a new figure and axes are created.

    Returns:
        matplotlib.axes.Axes: The axes object with the boxplot.
    """
    # --- 1. Setup and Data Preparation ---
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 7))

    # Create a color mapping dictionary from the color_df
    try:
        color_map = color_df['color'].to_dict()
    except KeyError:
        raise KeyError("The 'color_df' must have a column named 'color'.")

    # Get unique groups for the x-axis and for coloring
    x_groups = sorted(df[x_group_col].unique())
    color_groups = sorted(df[color_group_col].unique())
    n_color_groups = len(color_groups)
    
    # --- 2. Calculate Box Positions ---
    total_group_width = 1.0
    box_width = total_group_width / n_color_groups
    
    # Store data and positions for plotting
    data_to_plot = []
    positions = []
    box_colors = []

    # --- 3. Gather Data for Plotting ---
    # Iterate over each x-axis group
    for i, x_group in enumerate(x_groups):
        # Iterate over each color group to position it within the x-axis group
        for j, c_group in enumerate(color_groups):
            # Calculate the center position of this specific box
            offset = (j - (n_color_groups - 1) / 2.0) * box_width
            pos = i + offset
            
            # Filter the dataframe to get the data for this specific box
            data = df[(df[x_group_col] == x_group) & (df[color_group_col] == c_group)][data_col].dropna()

            if not data.empty:
                data_to_plot.append(data)
                positions.append(pos)
                if c_group not in color_map:
                    raise KeyError(f"Color group '{c_group}' not found in the color_df index.")
                box_colors.append(color_map[c_group])

    # --- 4. Plotting ---
    if not data_to_plot:
        ax.text(0.5, 0.5, "No data to plot.", ha='center', va='center', transform=ax.transAxes)
        return ax
        
    # make central line black
    bp = ax.boxplot(data_to_plot,
                    positions=positions,
                    widths=box_width * 0.9,
                    patch_artist=True,
                    manage_ticks=False,
                    boxprops=dict(facecolor='lightgray', edgecolor='black'),
                    medianprops=dict(color='black', linewidth=1.5),
                    whiskerprops=dict(color='black', linewidth=1.5),
                    capprops=dict(color='black', linewidth=1.5),
                    flierprops=dict(marker='o', color='red', markersize=5, alpha=0.5),
                    showfliers=True,
                    showmeans=False,
                    meanline=False,
                    notch=False,
                    bootstrap=None,
                    conf_intervals=None,
                    showcaps=True,
                    showbox=True,
                    )

    # --- 5. Customization (Colors and Labels) ---
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('black')

    ax.set_xticks(range(len(x_groups)))
    ax.set_xticklabels(x_groups)
    ax.set_xlabel(x_group_col)
    ax.set_ylabel(data_col)

    # --- 6. Add vertical lines between groups ---
    for pos in range(len(x_groups) - 1):
        ax.axvline(x=pos + 0.5, color='black', linestyle='--', linewidth=0.8)
    
    # legend_elements = [Patch(facecolor=color_map[c_group], edgecolor='black', label=c_group) 
    #                    for c_group in color_groups]
    # ax.legend(handles=legend_elements, title=color_group_col, bbox_to_anchor=(1.05, 1), loc='upper left')

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    return ax