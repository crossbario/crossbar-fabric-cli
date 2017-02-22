utest:
	py.test test/

test:
	python -m cdc.main node mynode3 list workers
	echo '{}' | python -m cdc.main node mynode2 start router myrouter2 -
	python -m cdc.main node mynode3 list workers
	python -m cdc.main node mynode3 router myrouter2 list transports
	echo '{"type": "websocket", "endpoint": {"type": "tcp", "port": 5002}}' | python -m cdc.main node mynode2 router myrouter2 start transport mytransport1 -
	python -m cdc.main node mynode2 router myrouter2 list transports
	echo '{"type": "rawsocket", "endpoint": {"type": "tcp", "port": 5003}}' | python -m cdc.main node mynode2 router myrouter2 start transport mytransport2 -
	python -m cdc.main node mynode2 router myrouter2 list transports

list_workers:
	python -m cdc.main node mynode3 list workers

list_transports:
	python -m cdc.main node mynode3 router worker1 list transports

profile_worker:
	python -m cdc.main node mynode3 router worker1 profile --runtime=5 --prune_percent=5

test2:
	echo '{"type": "websocket", "endpoint": {"type": "tcp", "port": 7002}}' | python -m cdc.main node mynode2 router myrouter1 start transport mytransport3 -

test3:
	python -m cdc.main node mynode2 router myrouter1 start transport mytransport4 '{"type": "websocket", "endpoint": {"type": "tcp", "port": 7003}}'

test4:
	python -m cdc.main node mynode1 container worker2 profile --runtime=5 --prune_percent=20



test_help:
	python -m cdc.main --help

test_get_time:
	python -m cdc.main --profile=local get time

test_list_nodes:
	python -m cdc.main --profile=local list nodes

test_list_workers:
	python -m cdc.main --profile=local list workers "mynode1"

test_get_stats:
	python -m cdc.main --profile=local get stats "mynode1" "worker1"


clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -rf ./__pycache__
	-find . -name "*.pyc" -exec rm -f {} \;

# This will run pep8, pyflakes and can skip lines that end with # noqa
flake8:
	flake8 --ignore=E501 cdc

pep8:
	pep8 --statistics --ignore=E501 -qq .

pep8_show_e231:
	pep8 --select=E231 --show-source

autopep8:
	autopep8 -ri --aggressive --ignore=E501 .
