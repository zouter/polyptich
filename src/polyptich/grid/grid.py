import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Tuple

active_fig = None


class Element:
    """
    A basic element in a figure with a (top-left) position and dimensions
    """

    pos = None
    dim = None

    @property
    def width(self):
        return self.dim[0]

    @property
    def height(self):
        return self.dim[1]

    def initialize(self, fig):
        self.fig = fig


TITLE_HEIGHT = 0.3
AXIS_WIDTH = AXIS_HEIGHT = 0.0


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
            global active_fig
            if active_fig is not None:
                fig = active_fig
            else:
                fig = plt.gcf()
            
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


class Panel(Ax):
    pass


class Title(Panel):
    def __init__(self, label, dim=None):
        if dim is None:
            dim = (1, TITLE_HEIGHT)
        super().__init__(dim=dim)
        self.label = label
        self.ax.set_axis_off()
        self.ax.text(0.5, 0.5, label, ha="center", va="center", size="large")


class Wrap(Element):
    """
    Grid-like layout with a fixed number of columns that will automatically wrap panels in the next row

    Parameters
    ----------
            The number of columns in the grid. Defaults to 6.
        padding_width : float, optional
            The width padding between elements in the grid. Defaults to 0.5.
        padding_height : float, optional
            The height padding between elements in the grid. If not provided, it defaults to the value of padding_width. Defaults to None.
        margin_height : float, optional
            The height margin around the grid. Defaults to 0.5.
        margin_width : float, optional
            The width margin around the grid. Defaults to 0.5.
    """

    title = None
    fig = None

    def __init__(
        self,
        ncol: int = 6,
        padding_width: float = 0.5,
        padding_height: Optional[float] = None,
        margin_height: float = 0.5,
        margin_width: float = 0.5,
    ):
        self.ncol: int = ncol
        self.padding_width: float = padding_width
        self.padding_height: Optional[float] = (
            padding_height if padding_height is not None else padding_width
        )
        self.margin_width: float = margin_width
        self.margin_height: float = margin_height
        self.elements: List[Element] = []
        self.pos: Tuple[int, int] = (0, 0)

    def add(self, element: Element):
        """
        Add an element to the grid
        """
        self.elements.append(element)
        element.initialize(self.fig)
        return element

    def align(self):
        width = 0
        height = 0
        nrow = 1
        x = 0
        y = 0
        next_y = 0

        if self.title is not None:
            y += self.title.height

        for i, el in enumerate(self.elements):
            el.align()

            el.pos = (x, y)

            next_y = max(next_y, y + el.height + self.padding_height)
            height = max(height, next_y)

            width = max(width, x + el.width)

            if (self.ncol > 1) and ((i == 0) or (((i + 1) % (self.ncol)) != 0)):
                x += el.width + self.padding_width
            else:
                nrow += 1
                x = 0
                y = next_y

        if self.title is not None:
            self.title.dim = (width, self.title.dim[1])

        self.dim = (width, height)

    def set_title(self, label):
        if self.title is not None:
            try:
                self.title.ax.remove()
            except KeyError:
                pass
            except AttributeError:
                pass

        self.title = Title(label)

    def position(self, fig, pos=(0, 0)):
        pos = self.pos[0] + pos[0], self.pos[1] + pos[1]
        if self.title is not None:
            self.title.position(fig, pos)
        for el in self.elements:
            el.position(fig, pos)

    def __getitem__(self, key):
        return list(self.elements)[key]

    def get_bottom_left_corner(self):
        nrow = (len(self.elements) - 1) // self.ncol
        ix = (nrow) * self.ncol
        return self.elements[ix]


class WrapAutobreak(Wrap):
    """
    Wraps panels if the size exeeds a maximum width
    """

    title = None

    def __init__(
        self,
        max_width,
        max_n_row=-1,
        padding_width=0.5,
        padding_height=None,
        margin_height=0.5,
        margin_width=0.5,
    ):
        self.max_width = max_width
        self.max_n_row = max_n_row
        super().__init__(
            ncol=1,
            padding_width=padding_width,
            padding_height=padding_height,
            margin_height=margin_height,
            margin_width=margin_width,
        )

    def align(self):
        width = 0
        height = 0
        self.nrow = 1
        x = 0
        y = 0
        next_y = 0

        if self.title is not None:
            y += self.title.height
        for i, el in enumerate(self.elements):
            el.align()

            el.pos = (x, y)

            next_y = max(next_y, y + el.height + self.padding_height)
            height = max(height, next_y)

            width = max(width, x + el.width)

            x += el.width + self.padding_width

            if x > self.max_width:
                self.nrow += 1
                x = 0
                y = next_y

        if self.title is not None:
            self.title.dim = (width, self.title.dim[1])

        self.dim = (width, height)


class Grid(Element):
    """
    Grid layout with a fixed number of columns and rows
    """

    title = None

    def __init__(
        self,
        nrow: int = 1,
        ncol: int = 1,
        padding_width: float = 0.5,
        padding_height: Optional[float] = None,
        margin_height: float = 0.5,
        margin_width: float = 0.5,
    ) -> None:
        self.padding_width = padding_width
        self.padding_height = padding_height if padding_height is not None else padding_width
        self.margin_width = margin_width
        self.margin_height = margin_height
        self.elements: List[List[Optional[Element]]] = [
            [None for _ in range(ncol)] for _ in range(nrow)
        ]

        self.pos: Tuple[int, int] = (0, 0)

        self.nrow: int = nrow
        self.ncol: int = ncol

        self.paddings_height: List[Optional[float]] = [None] * (nrow)
        self.paddings_width: List[Optional[float]] = [None] * (ncol)

    def align(self):
        width = 0
        height = 0
        x = 0
        y = 0
        next_y = 0

        if self.title is not None:
            y += self.title.height

        widths = [0] * self.ncol
        heights = [0] * self.nrow

        assert len(self.paddings_height) == self.nrow, (
            len(self.paddings_height),
            self.nrow,
        )
        assert len(self.paddings_width) == self.ncol, (
            len(self.paddings_width),
            self.ncol,
        )

        for row, row_elements in enumerate(self.elements):
            for col, el in enumerate(row_elements):
                if el is not None:
                    el.align()
                    if el.width > widths[col]:
                        widths[col] = el.width
                    if el.height > heights[row]:
                        heights[row] = el.height

        for row, (row_elements, el_height) in enumerate(zip(self.elements, heights)):
            padding_height = self.paddings_height[min(row + 1, self.nrow - 1)]
            if padding_height is None:
                padding_height = self.padding_height

            x = 0
            for col, (el, el_width) in enumerate(zip(row_elements, widths)):
                if el is not None:
                    el.pos = (x, y)

                    next_y = max(next_y, y + el.height + padding_height)
                    height = max(height, next_y)

                    width = max(width, x + el.width)

                padding_width = self.paddings_width[min(col + 1, self.ncol - 1)]
                if padding_width is None:
                    padding_width = self.padding_width

                x += el_width + padding_width
            y += el_height + padding_height

        if self.title is not None:
            self.title.dim = (width, self.title.dim[1])

        self.dim = (width, height)

    def set_title(self, label):
        self.title = Title(label)

    def position(self, fig, pos=(0, 0)):
        pos = self.pos[0] + pos[0], self.pos[1] + pos[1]
        if self.title is not None:
            self.title.position(fig, pos)

        for row_elements in self.elements:
            for el in row_elements:
                if el is not None:
                    el.position(fig, pos)

    def __getitem__(self, index):
        if not isinstance(index, tuple):
            raise TypeError("index must be a tuple, not " + str(index))
        return self.elements[index[0]][index[1]]

    def __setitem__(self, index, v):
        row = index[0]
        col = index[1]

        if not isinstance(row, int) or not isinstance(col, int):
            raise TypeError("row and col must be integers")

        if row >= (self.nrow):
            # add new row(s)
            for i in range(self.nrow, row + 1):
                self.elements.append([None for _ in range(self.ncol)])
            self.nrow = row + 1
            self.paddings_height.append(None)

        if col >= (self.ncol):
            # add new col(s)
            for i in range(self.ncol, col + 1):
                for row_ in self.elements:
                    row_.append(None)
            self.ncol = col + 1
            self.paddings_width.append(None)

        self.elements[row][col] = v

    def add(self, el, row=0, column=0, padding_height=None, padding_width=None):
        self[row, column] = el
        if padding_height is not None:
            self.paddings_height[row] = padding_height
        if padding_width is not None:
            self.paddings_width[column] = padding_width
        return el

    def add_under(self, el, column=0, padding=None):
        if (self.nrow == 1) and self[0, 0] is None:
            row = 0
        else:
            row = self.nrow

        # get column index if column is a panel
        if "grid.Element" in column.__class__.__mro__.__repr__():
            try:
                print(row)
                column = np.array(self.elements).flatten().tolist().index(column) % self.ncol
            except ValueError as e:
                raise ValueError("The panel specified as column was not found in the grid") from e
        if not isinstance(column, int):
            raise TypeError("column must be an integer, not " + str(column))
        self[row, column] = el
        if padding is not None:
            self.paddings_height[row] = padding
        return el

    def add_right(self, el, row=0, padding=None):
        if (self.ncol == 1) and (self[0, 0] is None):
            column = 0
        else:
            if row < self.nrow:
                # get first empty element
                for i, el_ in enumerate(self.elements[row]):
                    if el_ is None:
                        column = i
                        break
                else:
                    column = self.ncol
            else:
                # if the row does not exist => col is just 0
                column = 0

        # get column index if row is a panel
        if "grid.Element" in row.__class__.__mro__.__repr__():
            try:
                row = np.array(self.elements).flatten().tolist().index(row) // self.ncol
            except ValueError as e:
                raise ValueError("The panel specified as row was not found in the grid") from e

        self[row, column] = el
        if padding is not None:
            self.paddings_width[column] = padding
        return el

    def get_panel_position(self, panel):
        for row, row_elements in enumerate(self.elements):
            for col, el in enumerate(row_elements):
                if el is panel:
                    return row, col

    def __iter__(self):
        for row in self.elements:
            for el in row:
                if el is not None:
                    yield el

    def get_bottom_left_corner(self):
        return self.elements[self.nrow - 1][0]


class _Figure(mpl.figure.Figure):
    """
    Figure but with panel support
    """

    main: Panel

    def __init__(self, main: Panel, *args, **kwargs):
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

    def savefig(self, *args, dpi=300, bbox_inches="tight", display=True, **kwargs):
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


def Figure(main: Element, *args, **kwargs):
    """
    Create a figure with panel support

    Parameters
    ----------
    main : Element
        The main panel of the figure. All other panels are a child of this panel
    """
    return plt.figure(*args, main=main, **kwargs, FigureClass=_Figure)
