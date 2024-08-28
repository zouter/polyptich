jupytext --to notebook README.py
jupyter nbconvert --to notebook --execute README.ipynb --output README.ipynb
jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags='{"hide-input"}' --to markdown README.ipynb --output README.md