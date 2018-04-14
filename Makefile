.PHONY: install test docs clean

default:
	@echo "Main targets: install, test, clean"


# cleanup all build artifacts
clean:
	-rm -rf ./build
	-rm -rf ./dist
	-rm -rf ./docs/_build
	-rm -rf ./tests/_build
	-rm -rf *.egg-info
	-rm -f ./.cbsh-history
	-rm -rf ./.pytest_cache


# install all dev tools and package in dev mode
install:
	pip install --no-cache -r requirements-dev.txt
	pip install --no-cache -e .

# install package only, as users (regular mode)
install_package:
	pip install --no-cache .

# to encrypt secret key material so that it can be inserted into .travis files,
# the travis tool is needed. install using this target.
# usage: /usr/local/bin/travis encrypt access_key_id="..."
install_travis:
	sudo apt install ruby-dev
	sudo gem install travis


# run all tests via Tox (this is also how tests are run on Travis)
test:
	tox -e flake8,yapf,mypy,pytest

test_flake8:
	tox -e flake8
	#flake8 --ignore=E501 cbsh sphinxcontrib

test_yapf:
	tox -e yapf
	#yapf -rd cbsh sphinxcontrib

test_mypy:
	tox -e mypy
	#mypy cbsh

test_pytest:
	tox -e pytest
	#pytest

# auto-format code - WARNING: this my change files, in-place!
autoformat:
	#autopep8 -ri --aggressive cbsh sphinxcontrib
	yapf -ri cbsh sphinxcontrib


# build documentation
docs:
	sphinx-build -b html ./docs ./docs/_build


# build source distribution and universal egg - which is what
# we publish to pypi
build_package:
	python setup.py sdist
	python setup.py bdist_wheel

# publish package to pypi: https://pypi.python.org/pypi/cbsh
publish_package_pypi: build_package
	twine upload dist/*

# publish package to crossbar s3
publish_package_crossbar: build_package
	aws s3 cp --acl public-read \
		./dist/cbsh-*.whl \
		s3://download.crossbario.com/cbsh/wheel/cbsh

publish_package: publish_package_crossbar publish_package_pypi


# build Linux exe
build_exe:
	pip install .
	pyinstaller \
		--clean \
		--onefile \
		--name cbsh \
		--hidden-import "cookiecutter.extensions" \
		--hidden-import "jinja2_time" \
		--hidden-import "sphinx.util.compat" \
		--hidden-import "sphinxcontrib.xbr" \
		cbsh/cli.py

# publish Linux exe to crossbar s3:
# https://s3.eu-central-1.amazonaws.com/download.crossbario.com/cbsh/linux/cbsh
publish_exe: build_exe
	aws s3 cp --acl public-read \
		./dist/cbsh \
		s3://download.crossbario.com/cbsh/linux/cbsh

# install Linux exe locally
install_exe: build_exe
	sudo cp ./dist/cbsh /usr/local/bin/cbsh
