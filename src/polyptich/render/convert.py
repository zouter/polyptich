import click
from polyptich import paths
import pathlib
import subprocess
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter

@click.command()
@click.argument('file', required = True)
def convert(file):
    file = pathlib.Path(file).absolute().resolve()
    if not file.exists():
        raise FileNotFoundError(file)
    
    output_ipynb = (paths.get_results() / file.relative_to(paths.get_code())).with_suffix('.ipynb')
    output_html = (paths.get_results() / file.relative_to(paths.get_code())).with_suffix('.html')

    subprocess.run(f'jupytext --to notebook {file} -o {output_ipynb}', shell=True, check=True)

    print(f'Executing {output_ipynb}')
    with open(output_ipynb) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600)
    ep.preprocess(nb, {'metadata': {'path': paths.get_code()}})
    
    # write html
    print (f'Writing {output_html}')
    html_exporter = HTMLExporter(template_name="lab")
    (body, resources) = html_exporter.from_notebook_node(nb)
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(body)

if __name__ == '__main__':
    convert()