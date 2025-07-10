import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import polyptich as pp
import jax
import jax.numpy as jnp
from functools import partial


@partial(jax.jit, static_argnames=["boundaries", "bandwidth", "grid_size"])
def kde_2d_reflection_jax(
    points: jnp.ndarray,
    boundaries: tuple,
    bandwidth: float,
    grid_size: int = 200,
):
    """
    Performant 2D Kernel Density Estimation with boundary correction using reflection (JAX version).

    Args:
        points (jnp.ndarray): A [N, 2] array of data points.
        boundaries (tuple): A tuple of (xmin, xmax, ymin, ymax).
        bandwidth (float): The bandwidth (h) of the Gaussian kernel.
        grid_size (int): The number of points in each dimension of the output grid.

    Returns:
        density (jnp.ndarray): A [grid_size, grid_size] array of the estimated density.
        grid_x (jnp.ndarray): The x-coordinates of the grid.
        grid_y (jnp.ndarray): The y-coordinates of the grid.
    """
    xmin, xmax, ymin, ymax = boundaries
    n_points = points.shape[0]

    # 1. Create 8 sets of reflected "ghost" points
    points_x, points_y = points[:, 0], points[:, 1]

    all_points = jnp.concatenate(
        [
            points,
            jnp.stack([2 * xmin - points_x, points_y], axis=1),  # Left
            jnp.stack([2 * xmax - points_x, points_y], axis=1),  # Right
            jnp.stack([points_x, 2 * ymin - points_y], axis=1),  # Bottom
            jnp.stack([points_x, 2 * ymax - points_y], axis=1),  # Top
            jnp.stack(
                [2 * xmin - points_x, 2 * ymin - points_y], axis=1
            ),  # Bottom-left
            jnp.stack(
                [2 * xmax - points_x, 2 * ymin - points_y], axis=1
            ),  # Bottom-right
            jnp.stack([2 * xmin - points_x, 2 * ymax - points_y], axis=1),  # Top-left
            jnp.stack([2 * xmax - points_x, 2 * ymax - points_y], axis=1),  # Top-right
        ]
    )

    # 2. Create the evaluation grid
    grid_x_vals = jnp.linspace(xmin, xmax, grid_size)
    grid_y_vals = jnp.linspace(ymin, ymax, grid_size)
    grid_x, grid_y = jnp.meshgrid(grid_x_vals, grid_y_vals, indexing="ij")
    grid_points = jnp.stack([grid_x.ravel(), grid_y.ravel()], axis=1)

    # 3. Perform KDE using broadcasting (the fast part)
    diff = jnp.expand_dims(grid_points, 1) - jnp.expand_dims(all_points, 0)
    sq_dist = jnp.sum((diff / bandwidth) ** 2, axis=2)

    kernel_vals = jnp.exp(-0.5 * sq_dist)

    density = jnp.sum(kernel_vals, axis=1).reshape(grid_size, grid_size)

    # 4. Normalize
    norm_factor = n_points * (bandwidth**2) * (2 * jnp.pi)
    density /= norm_factor

    return density, grid_x, grid_y


@partial(jax.jit, static_argnames=("grid_size",))
def kde_1d_reflection_jax(
    points: jnp.ndarray,
    boundaries: tuple,
    bandwidth: float,
    grid_size: int = 200,
):
    """
    Performant 1D Kernel Density Estimation with boundary correction using reflection.
    """
    xmin, xmax = boundaries
    n_points = points.shape[0]

    # Reflect points across the two boundaries
    reflected_pts = jnp.concatenate([points, 2 * xmin - points, 2 * xmax - points])

    # Create the evaluation grid
    grid_points = jnp.linspace(xmin, xmax, grid_size)

    # Perform KDE using broadcasting
    diff = jnp.expand_dims(grid_points, 1) - jnp.expand_dims(reflected_pts, 0)
    sq_dist = (diff / bandwidth) ** 2
    kernel_vals = jnp.exp(-0.5 * sq_dist)
    density = jnp.sum(kernel_vals, axis=1)

    # Normalize
    norm_factor = n_points * bandwidth * jnp.sqrt(2 * jnp.pi)
    density /= norm_factor

    return density, grid_points


# %%
def plot_density(ax, xx, yy, density, levels=20, cmap="magma"):
    """Plot the contour density on the given axis."""
    ax.contourf(xx, yy, density, levels=levels, cmap=cmap)
    ax.contour(xx, yy, density, colors="k", linewidths=0.5, levels=levels, alpha=0.5)
    ax.set_xlabel("")
    ax.set_ylabel("")


from itertools import combinations


# Main logic
def plot_all_pairwise_kde(
    Z, boundaries, bandwidth, labels=None, diag_kind="kde", grid_size=200
):
    """
    Generates a corner plot of pairwise 2D KDEs with 1D distributions on the diagonal,
    using the polyptich library structure.

    Args:
        Z (jnp.ndarray): The data matrix [n_samples, n_features].
        boundaries (tuple): A tuple of (min_val, max_val) for all features.
        bandwidth (float): The KDE bandwidth.
        labels (list, optional): Names for the features/variables.
        diag_kind (str, optional): 'kde' or 'hist' for the diagonal.
        grid_size (int, optional): Resolution of the KDE grid.
    """
    n_cols = Z.shape[1]
    xmin, xmax = boundaries
    if labels is None:
        labels = [f"{i}" for i in range(n_cols)]

    # 1. Pre-calculate all 2D KDEs to find a common color scale
    print("Calculating 2D KDEs...")
    pairs = list(combinations(range(n_cols), 2))
    kde_2d_data = {}
    for i1, i2 in pairs:
        z_pair = Z[:, [i1, i2]]
        z_pair = z_pair[~np.isnan(z_pair).any(axis=1)]
        print(len(z_pair))
        density, xx, yy = kde_2d_reflection_jax(
            z_pair,
            boundaries=(xmin, xmax, xmin, xmax),
            bandwidth=bandwidth,
            grid_size=grid_size,
        )
        density.block_until_ready()  # Ensure calculation is finished
        if len(z_pair) == 0:
            xx = np.linspace(xmin, xmax, grid_size)
            yy = np.linspace(xmin, xmax, grid_size)
            density = np.zeros((grid_size, grid_size))
        kde_2d_data[(i1, i2)] = (xx, yy, density)

    # Determine shared levels for a consistent color bar across all 2D plots
    max_density = 0
    if kde_2d_data:  # Handle case with only one dimension
        max_density = np.max([d[2].max() for d in kde_2d_data.values()])
    levels = np.linspace(0, max_density, 30)
    cmap = mpl.colormaps["magma"]

    # 2. Set up the polyptich figure and grid
    # The grid must be n_cols x n_cols to accommodate the diagonal
    fig = pp.grid.Figure(pp.grid.Grid(padding_width=0.02, padding_height=0.02))

    # 3. Loop through the grid and populate the panels
    print("Populating grid panels...")
    for i in range(n_cols):  # Row index
        for j in range(n_cols):  # Column index
            # We only populate the lower triangle and the diagonal
            if j > i:
                continue

            # --- Diagonal Plots (1D Distributions) ---
            if i == j:
                ax = fig.main[i, j] = pp.grid.Panel((1, 1))
                z_uni = Z[:, i]
                z_uni = z_uni[~np.isnan(z_uni)]

                if diag_kind == "kde":
                    density_1d, xx_1d = kde_1d_reflection_jax(
                        z_uni,
                        boundaries=boundaries,
                        bandwidth=bandwidth,
                        grid_size=grid_size,
                    )
                    ax.fill_between(xx_1d, 0, density_1d, color=cmap(0.6), lw=0)
                    ax.plot(xx_1d, density_1d, color="k", lw=1.2)
                elif diag_kind == "hist":
                    ax.hist(
                        np.asarray(z_uni),
                        bins=40,
                        range=boundaries,
                        density=True,
                        color=cmap(0.6),
                        histtype="stepfilled",
                        ec="k",
                        lw=1.2,
                    )

                ax.set_xlim(boundaries)
                ax.set_ylim(bottom=0)
                # Add variable label to the diagonal plot
                ax.text(
                    0.5,
                    0.5,
                    labels[i],
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    fontsize=12,
                    weight="bold",
                )

            # --- Off-Diagonal Plots (2D KDEs) ---
            else:  # Here j < i
                ax = fig.main[i, j] = pp.grid.Panel((1, 1))
                # Retrieve the pre-calculated data
                xx, yy, density = kde_2d_data[(j, i)]
                plot_density(ax, xx, yy, density, levels=levels, cmap=cmap)
                ax.set_xlim(boundaries)
                ax.set_ylim(boundaries)

            # 4. Handle Axis Labels and Ticks for a clean look
            # By default, turn all ticks off. We'll turn them on for the outer edge.
            ax.set_xticks([])
            ax.set_yticks([])

            # Show Y-labels and ticks ONLY on the leftmost column (j=0)
            if j == 0 and i > 0:
                ax.set_ylabel(labels[i])

            # Show X-labels and ticks ONLY on the bottom row (i=n_cols-1)
            if i == n_cols - 1:
                ax.set_xlabel(labels[j])

    return fig



def plot_corner_kde(
    Z, boundaries, bandwidth, labels=None, diag_kind="kde", grid_size=200, panel_size = 1, panel_size_1d = 0.3
):
    """
    Generates a corner plot of pairwise 2D KDEs with 1D distributions on the
    left and bottom margins.

    Args:
        Z (jnp.ndarray): The data matrix [n_samples, n_features].
        boundaries (tuple): A tuple of (min_val, max_val) for all features.
        bandwidth (float): The KDE bandwidth.
        labels (list, optional): Names for the features/variables.
        diag_kind (str, optional): 'kde' or 'hist' for the marginal plots.
        grid_size (int, optional): Resolution of the KDE grid.
    """
    n_cols = Z.shape[1]
    xmin, xmax = boundaries
    if labels is None:
        labels = [f"P{i+1}" for i in range(n_cols)]

    # 1. Pre-calculate all 2D KDEs
    pairs = list(combinations(range(n_cols), 2))
    kde_2d_data = {}
    for i1, i2 in pairs:
        z_pair = Z[:, [i1, i2]]
        # Remove any rows with NaN in this pair
        z_pair = z_pair[~jnp.isnan(z_pair).any(axis=1)]
        if len(z_pair) == 0:
            xx = jnp.linspace(xmin, xmax, grid_size)
            yy = jnp.linspace(xmin, xmax, grid_size)
            density = jnp.zeros((grid_size, grid_size))
        else:
            density, xx, yy = kde_2d_reflection_jax(
                z_pair,
                boundaries=(xmin, xmax, xmin, xmax),
                bandwidth=bandwidth,
                grid_size=grid_size,
            )
        density.block_until_ready()
        kde_2d_data[(i1, i2)] = (xx, yy, density)

    max_density = 0
    if kde_2d_data:
        max_density = np.max([d[2].max() for d in kde_2d_data.values()])
    levels = np.linspace(0, max_density, 30)
    cmap = mpl.colormaps["magma"]

    # 2. Set up the polyptich figure with LEFT and BOTTOM margins
    grid = pp.grid.Grid(
        padding_width=0.02,
        padding_height=0.02,
    )
    fig = pp.grid.Figure(grid)

    # 3. Populate the grid panels
    # --- Off-Diagonal Plots (2D KDEs in the lower triangle) ---
    for i in range(n_cols):      # Row index
        for j in range(i):       # Column index (j < i)
            ax = fig.main[i+1, j+1] = pp.grid.Panel((panel_size, panel_size))
            xx, yy, density = kde_2d_data[(j, i)]
            plot_density(ax, xx, yy, density, levels=levels, cmap=cmap)
            
            # --- Ticks and Limits ---
            ax.set_xlim(boundaries)
            ax.set_ylim(boundaries)
            ax.set_xticks([])
            ax.set_yticks([])

    # --- Populate the Bottom Margin (1D Horizontal Plots) ---
    for j in range(n_cols-1):        
        ax = fig.main[n_cols+1, j+1] = pp.grid.Panel((panel_size, panel_size_1d))
        z_uni = Z[:, j]
        z_uni = z_uni[~jnp.isnan(z_uni)]

        if diag_kind == "kde":
            density_1d, xx_1d = kde_1d_reflection_jax(
                z_uni, boundaries, bandwidth, grid_size
            )
            ax.fill_between(xx_1d, 0, density_1d, color=cmap(0.6), lw=0)
            ax.plot(xx_1d, density_1d, color="k", lw=1.2)
        else: # hist
            ax.hist(np.asarray(z_uni), bins=40, range=boundaries, density=True, color=cmap(0.6))

        ax.set_xlim(boundaries)
        ax.set_ylim(bottom=0)
        ax.set_yticks([]) # Hide y-ticks
        ax.set_xticks([]) # Hide y-ticks
        ax.set_xlabel(labels[j]) # Add label here

    # --- Populate the Left Margin (1D Vertical Plots) ---
    for i in range(1, n_cols):
        ax = fig.main[i+1, 0] = pp.grid.Panel((panel_size_1d, panel_size))
        z_uni = Z[:, i]
        z_uni = z_uni[~jnp.isnan(z_uni)]

        if diag_kind == "kde":
            density_1d, yy_1d = kde_1d_reflection_jax(
                z_uni, boundaries, bandwidth, grid_size
            )
            # Swap x and y for vertical orientation!
            ax.fill_betweenx(yy_1d, 0, density_1d, color=cmap(0.6), lw=0)
            ax.plot(density_1d, yy_1d, color="k", lw=1.2)
        else: # hist
             ax.hist(np.asarray(z_uni), bins=40, range=boundaries, density=True,
                     color=cmap(0.6), orientation='horizontal')

        ax.set_ylim(boundaries)
        ax.set_xlim(left=0)
        ax.set_xticks([]) # Hide x-ticks
        ax.set_yticks([]) # Hide x-ticks
        ax.set_ylabel(labels[i]) # Add label here


    return fig