#####################################################################################
#
#  Copyright (c) Crossbar.io Technologies GmbH
#
#  Unless a separate license agreement exists between you and Crossbar.io GmbH (e.g.
#  you have purchased a commercial license), the license terms below apply.
#
#  Should you enter into a separate license agreement after having received a copy of
#  this software, then the terms of such license agreement replace the terms below at
#  the time at which such license agreement becomes effective.
#
#  In case a separate license agreement ends, and such agreement ends without being
#  replaced by another separate license agreement, the license terms below apply
#  from the time at which said agreement ends.
#
#  LICENSE TERMS
#
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License, version 3, as published by the
#  Free Software Foundation. This program is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#
#####################################################################################

import os
from six.moves import configparser

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
        return u'Profile(name={}, url={}, reconnect={}, debug={}, realm={}, role={}, pubkey={},' \
               u'privkey={})'.format(self.name, self.url, self.reconnect, self.debug, self.realm,
                                     self.role, self.pubkey, self.privkey)

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
                Profile.log.warn('unprocessed config attribute "{}"'.format(k))

        return Profile(name, url, reconnect, debug, realm, role, pubkey, privkey)


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
