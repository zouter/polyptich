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