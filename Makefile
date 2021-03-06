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

distclean: clean
	-rm -rf ./.tox
	-rm -rf ./.mypy_cache


# install dev & test requirements
test_requirements:
	pip install --upgrade pip
	pip install --no-cache -r requirements-dev.txt

# install package in dev mode
install:
	pip install --no-cache -e .

# install package in regular mode
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
	tox
	#tox .-e flake8,yapf,mypy,pytest

test_sphinx:
	tox -e sphinx

test_flake8:
	tox -e flake8

test_yapf:
	tox -e yapf

test_mypy:
	tox -e mypy

test_pylint:
	tox -e pylint

test_pytest:
	tox -e pytest


# auto-format code - WARNING: this my change files, in-place!
autoformat:
	#autopep8 -ri --aggressive cbsh
	yapf -ri -e cbsh/reflection cbsh


# build documentation
docs:
	sphinx-build -b html ./docs ./docs/_build

# spellcheck the docs
docs_spelling:
	sphinx-build -b spelling -d ./docs/_build/doctrees ./docs ./docs/_build/spelling
	#sphinx-build -b spelling -d build/doctrees   source build/spelling

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



#
# XBR IDL related targets
#

# flatc compiler to use
FLATC=${HOME}/scm/xbr/flatbuffers/flatc -I ${HOME}/scm/wamp-proto/wamp-proto/rfc/flatbuffers/
#FLATC=flatc

# generate schema type library (.bfbs binary)
# input .fbs files for schema
#
REFLECTION_SCHEMA_FILE=cbsh/idl/reflection.fbs

reflection:
	cp ../../xbr/flatbuffers/reflection/reflection.fbs $(REFLECTION_SCHEMA_FILE)
	$(FLATC) -o cbsh/idl/ --binary --schema --bfbs-comments --bfbs-builtins $(REFLECTION_SCHEMA_FILE)
	$(FLATC) -o cbsh/ --python $(REFLECTION_SCHEMA_FILE)

reflection_bindings: reflection
	$(FLATC) -o cbsh --python $(REFLECTION_SCHEMA_FILE)
	find cbsh/idl/


# process example IDL files
#
TEST_IDL_FILES=tests/idl/example.fbs

test_idl: test_idl_schema test_idl_full test_idl_cloc

test_idl_schema:
	$(FLATC) -o tests/idl/_build --binary --schema --bfbs-comments --bfbs-builtins $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/python --python $(TEST_IDL_FILES)
	python cbsh/idl/loader.py --verbose --outfile tests/idl/_build/example.json tests/idl/_build/example.bfbs

test_idl_full:
	$(FLATC) -o tests/idl/_build/cpp --cpp $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/csharp --csharp $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/go --go $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/java --java $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/js --js $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/php --php $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/python --python $(TEST_IDL_FILES)
	$(FLATC) -o tests/idl/_build/ts --ts $(TEST_IDL_FILES)

test_idl_cloc:
	cloc --read-lang-def=cloc.def tests/idl/_build

test_idl_generate:
	python cbsh/idl/generator.py --verbose tests/idl/_build/example.json
