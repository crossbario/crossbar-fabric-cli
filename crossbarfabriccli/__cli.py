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

import txaio
txaio.use_twisted()

import click
import json

import os

from crossbarfabriccli import __version__
from crossbarfabriccli.key import UserKey
from crossbarfabriccli.config import Config
from crossbarfabriccli.client import ClientSession
from os.path import expanduser, join, exists

import six
import sys
import argparse
from autobahn.twisted.wamp import ApplicationRunner


def pprint_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=4))


class CmdConfig(object):

    debug = True


@click.group(help="Crossbar.io Fabric Command Line")
@click.option(
    '--profile', envvar='CBF_PROFILE', default=None,
    help="Set the profile to be used",
)
@click.option(
    '--realm', envvar='CBF_REALM', default=None,
    help="Override the realm to join",
)
@click.option(
    '--role', envvar='CBF_ROLE', default=None,
    help="Override the role requested on the realm to join",
)
@click.option(
    '--debug', '-d', 'debug',
    flag_value=True,
    default=False,
    help="Enable debug and development mode.",
)
@click.option(
    '--json', default=False,
    is_flag=True,
    help='Output in json instead of text',
)
@click.pass_context
def main(ctx, profile, realm, role, debug, json):
    cfg = CmdConfig()
    cfg.profile = profile
    cfg.realm = realm
    cfg.role = role
    cfg.debug = debug
    cfg.output = 'json' if json else 'text'

    # remember parameters in CLI context
    ctx.obj = cfg


@main.command()
@click.pass_obj
def version(cfg):
    if cfg.output == 'text':
        print("Crossbar.io Fabric CLI version: {}".format(__version__))
    elif cfg.output == 'json':
        pprint_json({u'version': __version__})
    else:
        raise Exception('internal error')


def _init_cbf_dir(dotdir=None, profile=None):

    dotdir = dotdir or '~/.cbf'
    profile = profile or 'default'

    cbf_dir = expanduser(dotdir)
    if not os.path.isdir(cbf_dir):
        os.mkdir(cbf_dir)

    config_path = os.path.join(cbf_dir, 'config')
    config = Config(config_path)

    profile_obj = config.profiles.get(profile, None)
    if not profile_obj:
        raise click.ClickException('no such profile: "{}"'.format(profile))

    privkey_path = os.path.join(cbf_dir, profile_obj.privkey or 'default.priv')
    pubkey_path = os.path.join(cbf_dir, profile_obj.pubkey or 'default.pub')
    key = UserKey(privkey_path, pubkey_path)

    return key, profile_obj

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.task import react

def connect(reactor, on_success, on_error, url, realm, extra):
    done = Deferred()
    done.addCallbacks(on_success, on_error)
    extra[u'done'] = done

    runner = ApplicationRunner(url=url, realm=realm, extra=extra)
    runner.run(ClientSession, start_reactor=False, auto_reconnect=False)

    return done


@main.command()
@click.option(
    '--code', default=None,
    help="Supply login/registration code",
)
@click.pass_obj
@inlineCallbacks
def login(cfg, code):
    key, profile = _init_cbf_dir(profile=cfg.profile)

    #click.echo('using profile: {}'.format(profile))
    #click.echo('using key: {}'.format(key))

    realm = cfg.realm or profile.realm or u'fabric'
    authrole = cfg.role or profile.role or None
    authid = key.user_id

    url = u'ws://localhost:8080/ws'

    extra = {
        u'authid': authid,
        u'authrole': authrole,
        u'cfg': cfg,
        u'key': key,
        u'profile': profile,
        u'activation_code': code,
    }
    #click.echo('connecting to {}: realm={}, authid={}'.format(url, realm, authid))

    if cfg.debug:
        txaio.start_logging(level='debug')

    def success(details):
        print('login successful: realm={}, authid={}, authrole={}'.format(details.realm, details.authid, details.authrole))

    def error(err):
        print('login failed: {}'.format(err))

    react(connect, (success, error, url, realm, extra))
