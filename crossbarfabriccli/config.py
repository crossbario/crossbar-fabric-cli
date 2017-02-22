import os
from six.moves import configparser
import click

# pair a node from a node public key from a local file:
#
# cbf pair node --realm "myrealm" --node "mynode" /var/local/crossbar/.crossbar/key.pub

# pair a node from a node public key served from a HTTP URL:
#
# cbf pair node --realm "myrealm" --node "mynode" http://localhost:9140/key.pub

from txaio import make_logger


class Profile(object):

    log = make_logger()

    def __init__(self, name=None, reconnect=None, debug=None, realm=None, role=None, pubkey=None, privkey=None):
        self.name = name
        self.reconnect = reconnect
        self.debug = debug
        self.realm = realm
        self.role = role
        self.pubkey = pubkey
        self.privkey = privkey

    def __str__(self):
        name = u'u"{}"'.format(self.name) if self.name else u'None'
        return u'Profile(name={}, reconnect={}, debug={}, realm={}, role={}, pubkey={}, privkey={})'.format(name, self.reconnect, self.debug, self.realm, self.role, self.pubkey, self.privkey)

    @staticmethod
    def parse(name, items):
        reconnect = None
        debug = None
        realm = None
        role = None
        pubkey = None
        privkey = None
        for k, v in items:
            if k == 'reconnect':
                reconnect = int(v)
            elif k == 'debug':
                debug = bool(v)
            elif k == 'realm':
                realm = str(v)
            elif k == 'role':
                role = str(v)
            elif k == 'pubkey':
                pubkey = str(v)
            elif k == 'privkey':
                privkey = str(v)
            else:
                # skip unknown attribute
                self.log.warn('unprocessed config attribute "{}"'.format(k))

        profile = Profile(name, reconnect, debug, realm, role, pubkey, privkey)

        return profile

DEFAULT_CONFIG = """
[default]

privkey=default.priv
pubkey=default.pub
"""

class Config(object):

    log = make_logger()

    def __init__(self, config_path):
        self._config_path = os.path.abspath(config_path)
        self._load_and_maybe_generate(self._config_path)

    def _load_and_maybe_generate(self, config_path):

        if not os.path.isfile(config_path):
            with open(config_path, 'w') as f:
                f.write(DEFAULT_CONFIG)

        config = configparser.ConfigParser()
        config.read(config_path)

        self.config = config

        profiles = {}
        for profile_name in config.sections():
            profile = Profile.parse(profile_name, config.items(profile_name))
            self.log.debug('profile parsed: {}'.format(profile))
            profiles[profile_name] = profile

        self.profiles = profiles

        self.log.debug('profiles loaded for: {}'.format(sorted(self.profiles.keys())))
