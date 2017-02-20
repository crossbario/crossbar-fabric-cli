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
    help="Set the realm to be used",
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
def main(ctx, profile, realm, debug, json):
    cfg = CmdConfig()
    cfg.profile = profile
    cfg.realm = realm
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


@main.command()
@click.option(
    '--code', default=None,
    help="Supply login/registration code",
)
@click.pass_obj
def login(cfg, code):
    if cfg.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    key, profile = _init_cbf_dir(profile=cfg.profile)

    click.echo('using profile: {}'.format(profile))
    click.echo('using key: {}'.format(key))

    realm = cfg.realm or profile.realm or u'fabric'
    authid = key.user_id

    url = u'ws://localhost:8080/ws'

    extra = {
        u'authid': authid,
        u'authrole': None,
        u'cfg': cfg,
        u'key': key,
        u'profile': profile,
        u'activation_code': code
    }
    click.echo('connecting to {}: realm={}, authid={}'.format(url, realm, authid))

    runner = ApplicationRunner(url=url, realm=realm, extra=extra)
    runner.run(ClientSession)
