# a simple py.test based skeleton for unit-tests, using Click's testing support
import pytest

@pytest.fixture
def cfg():
    from cdc.altmain import Config
    return Config()

def test_wildcard(cfg):
    """
    ensure we match on a wildcard spec
    """
    from cdc.altmain import _filter_node_info

    node_info = {
        'node0': {
            'id': 'node0',
            'workers': [
                {
                    'id': 'worker0',
                    'transports': [
                        {'id': 'transport1'},
                        {'id': 'transport2'},
                        {'id': 'transport3'},
                    ]
                },
                {
                    'id': 'worker1',
                    'transports': [
                        {'id': 'transport1'},
                        {'id': 'transport2'},
                        {'id': 'transport3'},
                    ]
                },
            ]
        },
    }
    parts = ['node0', '', 'transport1']
    node_info = _filter_node_info(node_info, parts, cfg)

    #  we should only have "transport1" in transports now
    assert 'node0' in node_info
    node = node_info['node0']
    assert len(node['workers']) == 2
    for worker in node['workers']:
        assert len(worker['transports']) == 1
        assert worker['transports'][0]['id'] == 'transport1'
