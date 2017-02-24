clean:
	-rm -f ./.cbsh-history
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-find . -type d -name "__pycache__" -exec rm -rf {} \;
	-find . -name "*.pyc" -exec rm -f {} \;

install:
	pip install -e .

# This will run pep8, pyflakes and can skip lines that end with # noqa
flake8:
	flake8 --ignore=E501 cdc

pep8:
	pep8 --statistics --ignore=E501 -qq .

pep8_show_e231:
	pep8 --select=E231 --show-source

autopep8:
	autopep8 -ri --aggressive --ignore=E501 .
