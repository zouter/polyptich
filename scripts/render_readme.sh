jupytext --to notebook README.py
jupyter nbconvert --to notebook --execute README.ipynb --output README.ipynb
jupyter nbconvert --to markdown README.ipynb --output README.md