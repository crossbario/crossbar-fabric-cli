from txaio import make_logger

from autobahn.wamp import cryptosign

from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

from collections import OrderedDict
import os
import getpass
import socket

from autobahn.util import utcnow

import click
import re


class EmailAddress(click.ParamType):

    name = 'Email address'

    def __init__(self):
        click.ParamType.__init__(self)

    def convert(self, value, param, ctx):
        if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                    value):
            return value
        self.fail('invalid email address')



def _user_id():
    while True:
        value = click.prompt('Please enter your email address', type=EmailAddress())
        if click.confirm('We will send an activation code to this address "{}", right?'.format(value)):
            break

    return value


def _creator():
    """
    for informational purposes, try to identify the creator (user@hostname)
    """
    try:
        user = getpass.getuser()
    except:
        user = u'unknown'

    try:
        hostname = socket.gethostname()
    except:
        hostname = u'unknown'

    return u'{}@{}'.format(user, hostname)


def _write_node_key(filepath, tags, msg):
    """
    Internal helper.
    Write the given tags to the given file
    """
    with open(filepath, 'w') as f:
        f.write(msg)
        for (tag, value) in tags.items():
            if value:
                f.write(u'{}: {}\n'.format(tag, value))


def _parse_keyfile(key_path, private=True):
    """
    Internal helper. This parses a node.pub or node.priv file and
    returns a dict mapping tags -> values.
    """
    if os.path.exists(key_path) and not os.path.isfile(key_path):
        raise Exception("Key file '{}' exists, but isn't a file".format(key_path))

    allowed_tags = [u'public-key-ed25519', u'user-id', u'created-at',
                    u'creator']
    if private:
        allowed_tags.append(u'private-key-ed25519')

    tags = OrderedDict()
    with open(key_path, 'r') as key_file:
        got_blankline = False
        for line in key_file.readlines():
            if line.strip() == '':
                got_blankline = True
            elif got_blankline:
                tag, value = line.split(':', 1)
                tag = tag.strip().lower()
                value = value.strip()
                if tag not in allowed_tags:
                    raise Exception("Invalid tag '{}' in key file {}".format(tag, key_path))
                if tag in tags:
                    raise Exception("Duplicate tag '{}' in key file {}".format(tag, key_path))
                tags[tag] = value
    return tags


class UserKey(object):

    log = make_logger()

    def __init__(self, privkey, pubkey):

        self._privkey_path = privkey
        self._pubkey_path = pubkey

        self.key = None
        self._creator = None
        self._created_at = None
        self.user_id = None
        self._privkey = None
        self._privkey_hex = None
        self._pubkey = None
        self._pubkey_hex = None
        self._load_and_maybe_generate(self._privkey_path, self._pubkey_path)

    def __str__(self):
        return u'UserKey(privkey="{}", pubkey="{}" [{}])'.format(self._privkey_path, self._pubkey_path, self._pubkey_hex)

    def _load_and_maybe_generate(self, privkey_path, pubkey_path):

        if os.path.exists(privkey_path):

            # node private key seems to exist already .. check!

            priv_tags = _parse_keyfile(privkey_path, private=True)
            for tag in [u'creator', u'created-at', u'user-id', u'public-key-ed25519', u'private-key-ed25519']:
                if tag not in priv_tags:
                    raise Exception("Corrupt user private key file {} - {} tag not found".format(privkey_path, tag))

            creator = priv_tags[u'creator']
            created_at = priv_tags[u'created-at']
            user_id = priv_tags[u'user-id']
            privkey_hex = priv_tags[u'private-key-ed25519']
            privkey = SigningKey(privkey_hex, encoder=HexEncoder)
            pubkey = privkey.verify_key
            pubkey_hex = pubkey.encode(encoder=HexEncoder).decode('ascii')

            if priv_tags[u'public-key-ed25519'] != pubkey_hex:
                raise Exception(
                    ("Inconsistent user private key file {} - public-key-ed25519 doesn't"
                     " correspond to private-key-ed25519").format(pubkey_path)
                )

            if os.path.exists(pubkey_path):
                pub_tags = _parse_keyfile(pubkey_path, private=False)
                for tag in [u'creator', u'created-at', u'user-id', u'public-key-ed25519']:
                    if tag not in pub_tags:
                        raise Exception("Corrupt user public key file {} - {} tag not found".format(pubkey_path, tag))

                if pub_tags[u'public-key-ed25519'] != pubkey_hex:
                    raise Exception(
                        ("Inconsistent user public key file {} - public-key-ed25519 doesn't"
                         " correspond to private-key-ed25519").format(pubkey_path)
                    )
            else:
                self.log.info(
                    "User public key file {pub_path} not found - re-creating from user private key file {priv_path}",
                    pub_path=pubkey_path,
                    priv_path=privkey_path,
                )
                pub_tags = OrderedDict([
                    (u'creator', priv_tags[u'creator']),
                    (u'created-at', priv_tags[u'created-at']),
                    (u'user-id', priv_tags[u'user-id']),
                    (u'public-key-ed25519', pubkey_hex),
                ])
                msg = u'Crossbar.io user public key\n\n'
                _write_node_key(pubkey_path, pub_tags, msg)

            self.log.debug("User key already exists (public key: {hex})", hex=pubkey_hex)

        else:
            # user private key does not yet exist: generate one
            creator = _creator()
            created_at = utcnow()
            user_id = _user_id()
            privkey = SigningKey.generate()
            privkey_hex = privkey.encode(encoder=HexEncoder).decode('ascii')
            pubkey = privkey.verify_key
            pubkey_hex = pubkey.encode(encoder=HexEncoder).decode('ascii')

            # first, write the public file
            tags = OrderedDict([
                (u'creator', creator),
                (u'created-at', created_at),
                (u'user-id', user_id),
                (u'public-key-ed25519', pubkey_hex),
            ])
            msg = u'Crossbar.io Fabric user public key\n\n'
            _write_node_key(pubkey_path, tags, msg)

            # now, add the private key and write the private file
            tags[u'private-key-ed25519'] = privkey_hex
            msg = u'Crossbar.io Fabric user private key - KEEP THIS SAFE!\n\n'
            _write_node_key(privkey_path, tags, msg)

            self.log.info("New user key pair generated!")

        # fix file permissions on node public/private key files
        # note: we use decimals instead of octals as octal literals have changed between Py2/3
        if os.stat(pubkey_path).st_mode & 511 != 420:  # 420 (decimal) == 0644 (octal)
            os.chmod(pubkey_path, 420)
            self.log.info("File permissions on user public key fixed!")

        if os.stat(privkey_path).st_mode & 511 != 384:  # 384 (decimal) == 0600 (octal)
            os.chmod(privkey_path, 384)
            self.log.info("File permissions on user private key fixed!")

        # load keys into object
        self._creator = creator
        self._created_at = created_at
        self.user_id = user_id
        self._privkey = privkey
        self._privkey_hex = privkey_hex
        self._pubkey = pubkey
        self._pubkey_hex = pubkey_hex

        self.key = cryptosign.SigningKey(privkey)
