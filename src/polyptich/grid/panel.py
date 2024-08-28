from os import access
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Tuple

TITLE_HEIGHT = 0.3
AXIS_WIDTH = AXIS_HEIGHT = 0.0

from .element import Element

def move_axes(ax, fig, subplot_args = None, remove=False):
    """Move an Axes object from a figure to a new pyplot managed Figure in
    the specified subplot.
    
    ax = the original Axes
    fig = the new figure
    subplot_args = where to put the ax in the new figure, e.g. (nrows, ncols, index)
    """

    # get a reference to the old figure context so we can release it
    old_fig = ax.figure

    # remove the Axes from it's original Figure context
    # ax.remove()

    # set the pointer from the Axes to the new figure
    ax.figure = fig

    # add the Axes to the registry of axes for the figure
    # fig.axes.append(ax)
    # twice, I don't know why...
    # fig.add_axes(ax)

    # then to actually show the Axes in the new figure we have to make
    # a subplot with the positions etc for the Axes to go, so make a
    # subplot which will have a dummy Axes
    # dummy_ax = fig.add_subplot(*subplot_args)

    # then copy the relevant data from the dummy to the ax
    # ax.set_position(dummy_ax.get_position())

    # then remove the dummy
    # dummy_ax.remove()

    # close the figure the original axis was bound to
    if remove:
        plt.close(old_fig)
    else:
        return old_fig

class Ax(Element):
    """
    A panel with an axis

    Parameters
    ----------

    """

    ax2 = None
    insets = None
    fig = None

    def __init__(self, dim:tuple=None, pos:tuple=(0.0, 0.0), fig=None):
        self.dim = dim
        self.pos = pos
        self.ax = mpl.figure.Axes.__new__(mpl.figure.Axes)

        if fig is None:
            from .figure import get_figure
            fig = get_figure()
            if fig is None:
                raise ValueError("No figure found, first create a `polyptich.Figure` object")
            
        self.fig = fig
        self.ax.__init__(fig, [0, 0, 1, 1])

    def initialize(self, fig):
        pass
        
    @property
    def dim(self):
        return self._dim

    @dim.setter
    def dim(self, value):
        if len(value) != 2:
            raise ValueError("dim must be a tuple of length 2")
        if value[0] <= 0 or value[1] <= 0:
            raise ValueError("dim must be positive")
        self._dim = value

    @property
    def height(self):
        h = self.dim[1]

        # add some extra height if we have a title
        if self.ax.get_title() != "":
            h += TITLE_HEIGHT
        if self.ax.axison:
            h += AXIS_HEIGHT
        return h

    @height.setter
    def height(self, value):
        self.dim = (self.dim[0], value)

    @property
    def width(self):
        w = self.dim[0]
        if self.ax.axison:
            w += AXIS_WIDTH
        return w

    @width.setter
    def width(self, value):
        self.dim = (value, self.dim[1])

    def align(self):
        pass

    def position(self, fig, pos=(0, 0)):
        fig_width, fig_height = fig.get_size_inches()
        width, height = self.dim
        x, y = self.pos[0] + pos[0], self.pos[1] + pos[1]

        axes = [self.ax]
        if self.ax2 is not None:
            axes.append(self.ax2)

        for ax in axes:
            ax.set_position(
                [
                    x / fig_width,
                    (fig_height - y - height) / fig_height,
                    width / fig_width,
                    height / fig_height,
                ]
            )

            if ax.figure != fig:
                move_axes(ax, fig)

            fig.add_axes(ax)

        for inset, inset_position, inset_offset, inset_anchor in self.insets or []:
            inset.position(
                fig,
                pos=(
                    x
                    + (width - inset.dim[0]) * inset_anchor[0]
                    + (width) * inset_position[0]
                    + inset_offset[0],
                    y
                    + (height - inset.dim[1]) * inset_anchor[1]
                    + (height) * inset_position[1]
                    + inset_offset[1],
                ),
            )

    def add_twinx(self):
        global active_fig
        self.ax2 = mpl.figure.Axes(active_fig, [0, 0, 1, 1])
        self.ax2.xaxis.set_visible(False)
        self.ax2.patch.set_visible(False)
        self.ax2.yaxis.tick_right()
        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.set_offset_position("right")
        self.ax.yaxis.tick_left()
        return self.ax2

    def add_inset(self, inset, pos=(0, 0), offset=(0, 0), anchor=(0, 0)):
        if self.insets is None:
            self.insets = []
        self.insets.append([inset, pos, offset, anchor])
        return inset

    def __iter__(self):
        yield self
        yield self.ax

class Ax2(Element, mpl.figure.Axes):
    """
    A panel with an axis

    Parameters
    ----------
    dim : tuple
        The dimensions of the panel in inches

    """

    ax2 = None
    insets = None
    fig = None

    _tag = None

    def __init__(self, dim:tuple=None, pos:tuple=(0.0, 0.0), fig=None):
        self.dim = dim
        self.pos = pos
        self.ax = mpl.figure.Axes.__new__(mpl.figure.Axes)

        if fig is None:
            from .figure import get_figure
            fig = get_figure()
            if fig is None:
                raise ValueError("No figure found, first create a `polyptich.Figure` object")
            
        self.fig = fig

        super().__init__(fig, [0, 0, 1, 1])
        self.dim = dim

    def initialize(self, fig):
        pass
        
    @property
    def dim(self):
        return self._dim

    @dim.setter
    def dim(self, value):
        if len(value) != 2:
            raise ValueError("dim must be a tuple of length 2")
        if value[0] is not None and value[0] <= 0:
            raise ValueError("dim must be positive")
        if value[1] is not None and value[1] <= 0:
            raise ValueError("dim must be positive")
        self._dim = value

    @property
    def height(self):
        h = self.dim[1]

        if h is None:
            return None

        # add some extra height if we have a title
        if self.get_title() != "":
            h += TITLE_HEIGHT
        if self.axison:
            h += AXIS_HEIGHT
        return h

    @height.setter
    def height(self, value):
        self.dim = (self.dim[0], value)

    @property
    def width(self):
        w = self.dim[0]
        if w is None:
            return None
        if self.axison:
            w += AXIS_WIDTH
        return w

    @width.setter
    def width(self, value):
        self.dim = (value, self.dim[1])

    def align(self):
        pass

    def position(self, fig, pos=(0, 0)):
        fig_width, fig_height = fig.get_size_inches()
        width, height = self.dim
        x, y = self.pos[0] + pos[0], self.pos[1] + pos[1]

        axes = [self]
        if self.ax2 is not None:
            axes.append(self.ax2)

        for ax in axes:
            ax.set_position(
                [
                    x / fig_width,
                    (fig_height - y - height) / fig_height,
                    width / fig_width,
                    height / fig_height,
                ]
            )

            fig.add_axes(ax)

        for inset, inset_position, inset_offset, inset_anchor in self.insets or []:
            inset.position(
                fig,
                pos=(
                    x
                    + (width - inset.dim[0]) * inset_anchor[0]
                    + (width) * inset_position[0]
                    + inset_offset[0],
                    y
                    + (height - inset.dim[1]) * inset_anchor[1]
                    + (height) * inset_position[1]
                    + inset_offset[1],
                ),
            )

        if self._tag:
            self.annotate(
                self._tag,
                xy=(0.0, 1.),
                xytext=(-5, 5),
                xycoords="axes fraction",
                textcoords="offset points",
                ha="right",
                va="bottom",
                fontweight="bold",
            )

    def add_twinx(self):
        global active_fig
        self.ax2 = mpl.figure.Axes(active_fig, [0, 0, 1, 1])
        self.ax2.xaxis.set_visible(False)
        self.ax2.patch.set_visible(False)
        self.ax2.yaxis.tick_right()
        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.set_offset_position("right")
        self.ax.yaxis.tick_left()
        return self.ax2

    def add_inset(self, inset, pos=(0, 0), offset=(0, 0), anchor=(0, 0)):
        if self.insets is None:
            self.insets = []
        self.insets.append([inset, pos, offset, anchor])
        return inset

    def __iter__(self):
        yield self
        yield self

    def __or__(self, other):
        from .grid import Grid
        grid = Grid()
        grid[0, 0] = self
        grid[0, 1] = other
        return grid

    def __truediv__(self, other):
        from .grid import Grid
        if isinstance(other, Grid):
            other.shift_down(self)
            return other

        grid = Grid()
        grid[0, 0] = self
        grid[1, 0] = other
        return grid

    def add_tag(self, tag):
        self._tag = tag

    def add_title(self, title):
        self.set_title(title)

class Panel2(Ax2):
    pass

class Panel(Ax2):
    __doc__ = Ax2.__doc__
    pass


class Title(Panel):
    def __init__(self, label, dim=(None, 0.5), **kwargs):
        if dim is None:
            dim = (None, TITLE_HEIGHT)
        super().__init__(dim=dim)
        self.label = label
        self.set_axis_off()
        self.text(0.5, 0.5, label, ha="center", va="center", **{"size":"large", **kwargs})
