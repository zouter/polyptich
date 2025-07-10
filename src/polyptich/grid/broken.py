from polyptich.grid.panel import Panel
from polyptich.grid.grid import Grid
import numpy as np
import pandas as pd
import dataclasses
import matplotlib as mpl


@dataclasses.dataclass
class Breaking:
    """
    Breaking of a genome into distinct regions

    Parameters
    ----------
    regions : pd.DataFrame
        DataFrame with columns "start" and "end" defining the regions
    gap : int   
        Gap between regions in inches
    resolution : int
        Number of base pairs per inch
    """

    regions: pd.DataFrame

    gap: int = 0.05

    resolution: int = 2500

    @property
    def width(self):
        if "length" not in self.regions.columns:
            self.regions["length"] = self.regions["end"] - self.regions["start"]
        return (self.regions["length"] / self.resolution).sum() + self.gap * (len(self.regions) - 1)


class Broken(Grid):
    """
    A grid build from distinct regions that are using the same coordinate space
    """

    def __init__(self, breaking, height=0.5, margin_top=0.0, *args, **kwargs):
        super().__init__(padding_width=breaking.gap, margin_top=margin_top, *args, **kwargs)

        regions = breaking.regions

        regions["width"] = regions["end"] - regions["start"]
        regions["ix"] = np.arange(len(regions))

        for i, (region, region_info) in enumerate(regions.iterrows()):
            if "resolution" in region_info.index:
                resolution = region_info["resolution"]
            else:
                resolution = breaking.resolution
            subpanel_width = region_info["width"] / resolution
            panel, ax = self.add_right(
                Panel((subpanel_width, height + 1e-4)),
            )

            ax.set_xlim(region_info["start"], region_info["end"])
            ax.set_xticks([])
            ax.set_ylim(0, 1)
            if i != 0:
                ax.set_yticks([])
            if region_info["ix"] != 0:
                ax.spines.left.set_visible(False)
            if region_info["ix"] != len(regions) - 1:
                ax.spines.right.set_visible(False)
            ax.spines.top.set_visible(False)
            ax.set_facecolor("none")

            # ax.plot([0, 0], [0, 1], transform=ax.transAxes, color="k", lw=1, clip_on=False)


class BrokenGrid(Grid):
    """
    A grid build from distinct regions that are using the same coordinate space
    """

    def __init__(
        self, breaking, height=0.5, padding_height=0.05, margin_top=0.0, *args, **kwargs
    ):
        super().__init__(padding_width=breaking.gap, margin_top=margin_top, *args, **kwargs)

        regions = breaking.regions

        regions["width"] = regions["end"] - regions["start"]
        regions["ix"] = np.arange(len(regions))

        regions["panel_width"] = regions["width"] / breaking.resolution

        self.panel_widths = regions["panel_width"].values

        for i, (region, region_info) in enumerate(regions.iterrows()):
            _ = self.add_right(
                Grid(padding_height=padding_height, margin_top=0.0),
            )


def add_slanted_x(ax1, ax2, size=4, **kwargs):
    d = 1.0  # proportion of vertical to horizontal extent of the slanted line
    kwargs = dict(
        marker=[(-1, -d), (1, d)],
        markersize=size,
        linestyle="none",
        mew=1,
        clip_on=False,
        **{"color": "k", "mec": "k", **kwargs},
    )
    ax1.plot([1, 1], [0, 1], transform=ax1.transAxes, **kwargs)
    ax2.plot([0, 0], [0, 1], transform=ax2.transAxes, **kwargs)


class TransformBroken:
    def __init__(self, breaking):
        """
        Transforms from data coordinates to (broken) data coordinates

        Parameters
        ----------
        breaking : Breaking
        """

        regions = breaking.regions

        regions["width"] = regions["end"] - regions["start"]
        regions["ix"] = np.arange(len(regions))

        regions["cumstart"] = (np.pad(np.cumsum(regions["width"])[:-1], (1, 0))) + regions[
            "ix"
        ] * breaking.gap * breaking.resolution
        regions["cumend"] = (
            np.cumsum(regions["width"]) + regions["ix"] * breaking.gap * breaking.resolution
        )

        self.regions = regions
        self.resolution = breaking.resolution
        self.gap = breaking.gap

    def __call__(self, x):
        """
        Transform from data coordinates to (broken) data coordinates

        Parameters
        ----------
        x : float
            Position in data coordinates

        Returns
        -------
        float
            Position in (broken) data coordinates

        """

        assert isinstance(x, (int, float, np.ndarray, np.float64, np.int64))

        if isinstance(x, (int, float, np.float64, np.int64)):
            x = np.array([x])

        match = (x[:, None] >= self.regions["start"].values) & (
            x[:, None] <= self.regions["end"].values
        )

        argmax = np.argmax(
            match,
            axis=1,
        )
        allzero = (match == False).all(axis=1)

        # argmax[allzero] = np.nan

        y = self.regions.iloc[argmax]["cumstart"].values + (
            x - self.regions.iloc[argmax]["start"].values
        )
        y[allzero] = np.nan

        return y





class Expanding(Panel):
    """
    Shows all genes in the regions, with a "zoom-in" effect towards the regions of interest.

    Parameters:
        breaking1: polyptich.grid.Breaking
            Broken grid
        breaking2: polyptich.grid.Breaking
            Broken grid
        height: float
            Height of the expansion

    
    """
    def __init__(
        self,
        breaking1: Breaking,
        breaking2: Breaking,
        height: float = 0.2,
        **kwargs,
    ):
        width = max(breaking1.width, breaking2.width)

        if breaking1.width > breaking2.width:
            scale_top = 1
            scale_bottom = breaking2.width / breaking1.width
        else:
            scale_top = breaking1.width / breaking2.width
            scale_bottom = 1
        
        super().__init__((width, height), **kwargs)

        ax = self
        ax.axis("off")

        # breaking
        from polyptich.grid.broken import TransformBroken
        bt1 = TransformBroken(breaking1)
        bt2 = TransformBroken(breaking2)
        for i, (region, region_info) in enumerate(bt2.regions.iterrows()):
            y0 = 1.
            y1 = 1
            y2 = 0
            end1 = bt1(region_info["end"])[0] / breaking1.regions["cumend"].max() * scale_top
            start1 = bt1(region_info["start"])[0] / breaking1.regions["cumend"].max() * scale_top
            end2 = bt2(region_info["end"])[0] / breaking2.regions["cumend"].max() * scale_bottom
            start2 = bt2(region_info["start"])[0] / breaking2.regions["cumend"].max() * scale_bottom

            control_point_height = 0.5

            points = np.array([
                [end1, y0], # top right
                [end1, y1], # top right
                [end1, control_point_height], # bottom right P1
                [end2, control_point_height], # bottom right P2
                [end2, y2], # bottom right
                [start2,y2],   # bottom left
                [start2, control_point_height], # bottom left P1
                [start1, control_point_height], # bottom left P2
                [start1, y1], # bottom left
                [start1, y0], # top left
            ])

            # polygon
            # polygon = mpl.patches.Polygon(
            #     points,
            #     fc="#CCCCCC",
            #     lw=0.,
            #     zorder=-2,
            #     clip_on = False
            # )

            # smooth bezier path
            Path = mpl.path.Path

            path = mpl.path.Path(points, codes = [
                Path.MOVETO,
                Path.LINETO,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
                Path.LINETO,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
                Path.CLOSEPOLY
            ])
            
            polygon = mpl.patches.PathPatch(
                path,
                fc="#D6D6D6" if i % 2 == 0 else "#E6E6E6",
                lw=0.,
                zorder=-2,
                clip_on = False
            )
            ax.add_patch(polygon)