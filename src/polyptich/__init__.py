from . import grid
from .grid import Panel, Figure, Wrap, Grid, Title
from .utils import case_when
from . import paths


def setup_ipython():
    from IPython import get_ipython

    if get_ipython():
        get_ipython().run_line_magic("load_ext", "autoreload")
        get_ipython().run_line_magic("autoreload", "2")
        get_ipython().run_line_magic("config", "InlineBackend.figure_format = 'retina'")

        import os
        os.environ["ANYWIDGET_HMR"] = "1"

__all__ = ["grid", "case_when"]

