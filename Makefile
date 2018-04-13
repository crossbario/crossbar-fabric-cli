.PHONY: docs

default:
	@echo "targets: clean, install, flake8, upload"

clean:
	-rm -f ./.cbsh-history
	-rm -rf ./.tox
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -rf ./docs/_build
	-rm -rf ./tests/_build
	-rm -rf ./.pytest_cache
	-find . -type d -name "__pycache__" -exec rm -rf {} \;
	-find . -name "*.pyc" -exec rm -f {} \;

docs:
	sphinx-build -b html ./docs ./docs/_build

install:
	#pip install -r requirements-test.txt
	#pip install -r requirements-rtd.txt
	pip install -e .

travis:
	sudo apt install ruby-dev
	sudo gem install travis
	# /usr/local/bin/travis encrypt access_key_id="..."

# upload to our internal deployment system
upload: clean
	python setup.py bdist_wheel
	aws s3 cp --acl public-read \
		dist/cbsh-*.whl \
		s3://fabric-deploy/cbsh/

# This will run pep8, pyflakes and can skip lines that end with # noqa
flake8:
	flake8 --ignore=E501 cbsh

pep8:
	pep8 --statistics --ignore=E501 -qq .

pep8_show_e231:
	pep8 --select=E231 --show-source

autopep8:
	autopep8 -ri --aggressive --ignore=E501 .

# build a statically linked executable using Pyinstaller
build_linux_exe: clean
	python setup.py sdist
	docker build -t cbsh -f docker/Dockerfile .
	docker create --name cbsh-build cbsh
	docker cp cbsh-build:/build/dist/cbsh ./dist/
	docker rm --force cbsh-build
	docker rmi cbsh

build:
	python setup.py sdist
	python setup.py bdist_wheel


publish: build
	twine upload dist/*


#
# cbsh as a one-file executable (below is for Linux)
#

# install pyinstaller
exe_dev:
	pip install --no-cache --upgrade pyinstaller
	pip uninstall -y enum34

# build one-file executable using pyinstaller
exe_build: install
	pyinstaller \
		--clean \
		--onefile \
		--name cbsh \
		--hidden-import "cookiecutter.extensions" \
		--hidden-import "jinja2_time" \
		--hidden-import "sphinx.util.compat" \
		--hidden-import "sphinxcontrib.xbr" \
		cbsh/cli.py

# upload to S3:
# https://s3.eu-central-1.amazonaws.com/download.crossbario.com/cbsh/linux/cbsh
exe_upload: exe_build
	aws s3 cp --acl public-read \
		./dist/cbsh \
		s3://download.crossbario.com/cbsh/linux/cbsh

# install exe locally
exe_install: exe_build
	sudo mkdir -p /opt/cbsh/bin
	sudo cp ./dist/cbsh /opt/cbsh/bin/

# new release (do all of above)
exe_release: exe_install exe_upload
