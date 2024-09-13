jupytext --to notebook README.py
jupyter nbconvert --to notebook --execute README.ipynb --output README.ipynb
jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags='{"hide-input"}' --to markdown README.ipynb --output README.md

# Add the following URL to all locations of the image in README.md
sed -i 's|\!\[\([^]]*\)\](\([^)]*\))|\!\[\1\](https://github.com/zouter/polyptich/blob/master/\2?raw=True)|g' README.md
