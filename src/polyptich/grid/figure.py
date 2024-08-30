import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Tuple

from .element import Element
active_fig = None

class _Figure(mpl.figure.Figure):
    """
    Figure but with panel support

    Parameters
    ----------
    main
        The main panel of the figure. All other panels are a child of this panel.
    """

    main: Element

    def __init__(self, main: Element = None, *args, **kwargs):
        if main is None:
            from .grid import Grid

            main = Grid()
        self.main = main
        global active_fig
        active_fig = self
        self.plot_hooks = []
        super().__init__(*args, **kwargs)
        main.initialize(self)

    def plot(self):
        """
        Align and position all elements in the figure
        """

        self.main.align()
        self.set_size_inches(*self.main.dim)
        self.main.position(self)
        for hook in self.plot_hooks:
            hook()
        return self

    def set_tight_bounds(self):
        """
        Sets the bounds of the figure so that all elements are visible
        """
        new_bounds = self.get_tightbbox().extents
        current_size = self.get_size_inches()
        new_bounds[2] - new_bounds[0], new_bounds[3] - new_bounds[1]

        self.set_figwidth(new_bounds[2] - new_bounds[0])
        self.set_figheight(new_bounds[3] - new_bounds[1])

        for ax in self.axes:
            new_bbox = ax.get_position()
            current_axis_bounds = ax.get_position().extents
            new_bbox = mpl.figure.Bbox(
                np.array(
                    [
                        (current_axis_bounds[0] - (new_bounds[0] / current_size[0]))
                        / ((new_bounds[2] - new_bounds[0]) / current_size[0]),
                        (current_axis_bounds[1] - (new_bounds[1] / current_size[1]))
                        / ((new_bounds[3] - new_bounds[1]) / current_size[1]),
                        (current_axis_bounds[2] - (new_bounds[0] / current_size[0]))
                        / ((new_bounds[2] - new_bounds[0]) / current_size[0]),
                        (current_axis_bounds[3] - (new_bounds[1] / current_size[1]))
                        / ((new_bounds[3] - new_bounds[1]) / current_size[1]),
                    ]
                ).reshape((2, 2))
            )
            ax.set_position(new_bbox)

    def savefig(self, *args, dpi=100, bbox_inches="tight", display=True, **kwargs):
        self.plot()

        plt.close()

        super().savefig(*args, dpi=dpi, bbox_inches=bbox_inches, **kwargs)

        import IPython

        if IPython.get_ipython() is not None and display and not str(args[0]).endswith(".pdf"):
            IPython.display.display(IPython.display.Image(args[0], retina=True))

    def display(self):
        import tempfile

        file = tempfile.NamedTemporaryFile(suffix=".png")
        self.savefig(file.name, display=True)


def Figure(main: Element = None, *args, **kwargs):
    """
    Create a figure with panel support.

    Note that parameters such as `figsize` are useless here, as the size of the figure is determined by the panels in the figure.

    Parameters
    ----------
    main : Element
        The main panel of the figure. All other panels are a child of this panel. Defaults to a `polyptich.Grid()`
    """
    return plt.figure(*args, main=main, **kwargs, FigureClass=_Figure)

def get_figure():
    global active_fig
    return active_fig