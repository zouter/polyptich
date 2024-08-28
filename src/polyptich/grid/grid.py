import numpy as np
from typing import List, Optional, Tuple

from .element import Element
from .panel import Title


class Wrap(Element):
    """
    Grid-like layout with a fixed number of columns that will automatically wrap panels in the next row

    Parameters
    ----------
        ncol:
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
    Grid layout.

    Parameters
    ----------
    nrow:
        The number of rows in the grid. Defaults to 1.
    ncol:
        The number of columns in the grid. Defaults to 1.
    padding_width
        The width padding between elements in the grid. Defaults to 0.5. Note that this can be overridden for individual elements in the `add`, `add_under`, and `add_right` methods.
    padding_height
        The height padding between elements in the grid. If not provided, it defaults to the value of padding_width. Defaults to None.  Note that this can be overridden for individual elements in the `add`, `add_under`, and `add_right` methods.
    margin_height
        The height margin around the grid. Defaults to 0.5.
    margin_width
        The width margin around the grid. Defaults to 0.5.
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

        elements_to_auto_width = []
        elements_to_auto_height = []

        for row, row_elements in enumerate(self.elements):
            for col, el in enumerate(row_elements):
                if el is not None:
                    el.align()
                    if el.width is None:
                        elements_to_auto_width.append(el)
                    else:
                        if el.width > widths[col]:
                            widths[col] = el.width
                    if el.height is None:
                        elements_to_auto_height.append(el)
                    else:
                        if el.height > heights[row]:
                            heights[row] = el.height

        for el in elements_to_auto_width:
            el.width = max(widths)
        for el in elements_to_auto_height:
            el.height = max(heights)

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
            self.paddings_height.append(None)

        if col >= (self.ncol):
            # add new col(s)
            for i in range(self.ncol, col + 1):
                for row_ in self.elements:
                    row_.append(None)
            self.paddings_width.append(None)

        self.elements[row][col] = v

    def add(self, el, row=None, column=None, padding_height=None, padding_width=None, padding_height_up=None, padding_width_left=None):
        """
        Add an element to the grid

        Parameters
        ----------
        el:
            The element to add
        row:
            The row to add the element to. Defaults to 0.
        column:
            The column to add the element to. Defaults to 0.
        padding_height:
            The height padding between the element and the next element. If not provided, it defaults to the value of padding_width. Defaults to None.
        padding_width:
            The width padding between the element and the next element. Defaults to None.
        padding_height_up:
            The height padding between the element and the previous element. Defaults to None.
        padding_width_left:
            The width padding between the element and the previous element. Defaults to None.
        """

        # find first empty element
        if row is None:
            for i, row_elements in enumerate(self.elements):
                for j, el_ in enumerate(row_elements):
                    if el_ is None:
                        row = i
                        column = j
                        break
                else:
                    continue
                break
            else:
                row = self.nrow
                column = 0

        self[row, column] = el
        if padding_height is not None:
            self.paddings_height[row] = padding_height
        if padding_width is not None:
            self.paddings_width[column] = padding_width
        if padding_height_up is not None:
            self.paddings_height[row - 1] = padding_height_up
        if padding_width_left is not None:
            self.paddings_width[column - 1] = padding_width_left
        return el

    def add_under(self, el, column=0, padding=None, padding_up=None):
        """
        Add an element under another element

        Parameters
        ----------
        el:
            The element to add
        column:
            The column to add the element to. Defaults to 0. Can be an Element, in which case the column is determined by the position of the element in the grid.
        padding:
            The height padding between the element and the previous element.
        padding_up:
            The height padding between the element and the next element.
        """

        if (self.nrow == 1) and self[0, 0] is None:
            row = 0
        else:
            row = self.nrow

        # get column index if column is a panel
        if "grid.Element" in column.__class__.__mro__.__repr__():
            try:
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
        """
        Add an element to the right of another element

        Parameters
        ----------
        el:
            The element to add
        row:
            The row to add the element to. Defaults to 0. Can be an Element, in which case the row is determined by the position of the element in the grid.
        padding:
            The width padding between the element and the previous element.
        """

        # get row
        if "grid.Element" in row.__class__.__mro__.__repr__():
            try:
                row = np.array(self.elements).flatten().tolist().index(row) // self.ncol
            except ValueError as e:
                raise ValueError("The panel specified as row was not found in the grid") from e

        # get col
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

    def __or__(self, other):
        """
        Add a panel to the right of the grid
        """
        self.add_right(other)
        return self

    def __truediv__(self, other):
        """
        Add a panel under the grid
        """

        if isinstance(other, Grid):
            # merge grids
            row = self.nrow
            for i, row_elements in enumerate(other.elements):
                for j, el in enumerate(row_elements):
                    self[row + i, j] = el
            return self
        else:
            self.add_under(other)
            return self
        # grid = Grid(padding_height = 0.)
        # grid.add_under(self)
        # grid.add_under(other)
        return grid

    @property
    def nrow(self):
        return len(self.elements)

    @property
    def ncol(self):
        return len(self.elements[0])

    def shift_down(self, el):
        new_elements = [[el, *[None] * (self.ncol - 1)]]
        new_elements.extend(self.elements)

        self.paddings_height = [None, *self.paddings_height]

        self.elements = new_elements

        return self