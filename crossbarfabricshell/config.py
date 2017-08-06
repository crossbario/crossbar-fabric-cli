###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", fWITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

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

    def __init__(self, name=None, url=None, reconnect=None, debug=None, realm=None, role=None, pubkey=None, privkey=None):
        self.name = name
        self.url = url
        self.reconnect = reconnect
        self.debug = debug
        self.realm = realm
        self.role = role
        self.pubkey = pubkey
        self.privkey = privkey

    def __str__(self):
        return u'Profile(name={}, url={}, reconnect={}, debug={}, realm={}, role={}, pubkey={}, privkey={})'.format(self.name, self.url, self.reconnect, self.debug, self.realm, self.role, self.pubkey, self.privkey)

    @staticmethod
    def parse(name, items):
        url = None
        reconnect = None
        debug = None
        realm = None
        role = None
        pubkey = None
        privkey = None
        for k, v in items:
            if k == 'url':
                url = str(v)
            elif k == 'reconnect':
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

        profile = Profile(name, url, reconnect, debug, realm, role, pubkey, privkey)

        return profile


class UserConfig(object):

    log = make_logger()

    def __init__(self, config_path):
        self._config_path = os.path.abspath(config_path)

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
