python -m setuptools_git_versioning

version="0.0.7"

git add .
git commit -m "version v${version}"

git tag -a v${version} -m "v${version}"

python -m build

# optional: upload test
# twine upload --repository testpypi dist/polyptich-${version}.tar.gz --verbose

git push --tags

# conda install gh --channel conda-forge
gh release create v${version} -t "v${version}" -n "v${version}" dist/polyptich-${version}.tar.gz

# pip install twine
twine upload dist/polyptich-${version}.tar.gz --verbose

python -m build --wheel
