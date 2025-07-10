import click
from polyptich import paths
import pathlib
import nbconvert
import subprocess
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter

from .convert import convert

@click.command()
def synchronize():
    # ensure this is a git repo
    if not pathlib.Path('.git').exists():
        raise FileNotFoundError('.git')

    code = paths.get_code()
    if not code.exists():
        raise FileNotFoundError(code)

    results = paths.get_results()
    if not results.exists():
        results.mkdir()

    for code_subfolder in code.iterdir():
        if code_subfolder.is_dir():
            results_subfolder = results / code_subfolder.relative_to(code)
            if not results_subfolder.exists():
                results_subfolder.mkdir(parents=True)
            
