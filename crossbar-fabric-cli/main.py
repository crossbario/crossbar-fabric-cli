###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Tavendo GmbH
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
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from __future__ import absolute_import, print_function

import os
import sys
import json
import ConfigParser
from textwrap import fill, TextWrapper
from os.path import expanduser, join, exists
from pprint import pprint
from datetime import datetime
from functools import partial, wraps
from base64 import urlsafe_b64decode
from binascii import hexlify

import click
import six

from cdc import __version__
from cdc.util import pprint_json, logerr, print_vmprof
from cdc.session import run_commands
from cdc.command import CmdListNodes, CmdListWorkers, CmdListRouterTransports
from cdc.command import CmdGetTime
from cdc.command import CmdProfileWorker, CmdGetWorkerStats

from twisted.internet.defer import inlineCallbacks, Deferred, returnValue, DeferredList
from twisted.internet.task import react, LoopingCall
from twisted.python.failure import Failure

from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp import auth
from autobahn.wamp.exception import ApplicationError
from autobahn.websocket.util import parse_url

import humanize

HIGHLIGHT_FG = 'yellow'
HIGHLIGHT_BG = 'black'


# XXX:
#
# further cleanups:
# 1. create a ../command/* dir
# 2. move each command to e.g. command/activate.py etc
# 3. ...would have to arrange for things to be imported etc, perhaps
#    from __init__ or similar...


class CdcSession(ApplicationSession):
    def __init__(self, *args, **kw):
        super(CdcSession, self).__init__(*args, **kw)
        self._on_join = self.config.extra['on_join']

    def onConnect(self):
        authid = self.config.extra['user']
        realm = self.config.realm
        if self.config.extra['verbose']:
            print("Connected. Joining realm '{}' as '{}' ..".format(realm, authid))
        self.join(realm, [u"wampcra"], authid)

    def onChallenge(self, challenge):
        if challenge.method == u"wampcra":
            authkey = self.config.extra['key'].encode('utf8')
            signature = auth.compute_wcs(authkey, challenge.extra['challenge'].encode('utf8'))
            return signature.decode('ascii')
        else:
            raise Exception("don't know how to compute challenge for authmethod {}".format(challenge.method))

    def onJoin(self, details):
        self._on_join.callback((self, details))

    def onLeave(self, details):
        if not self._on_join.called:
            self._on_join.errback(Exception("Left without joining '{}'".format(details)))
        self.disconnect()


class Config(object):
    """
    Internal use. Populated from options, lives as the Click
    context.obj (decorate with @click.pass_obj to receive it)

    The class-level values in here are the defaults
    """

    debug = True # XXX
    verbose = False
    user = None
    key = None
    realm = None
    output = 'text'
    router = 'wss://cdc.crossbar.io'

    def __repr__(self):
        return "Config:\n  " + "  ".join(["{}={}\n".format(k, repr(v)) for (k, v) in self.__dict__.items() if not k.startswith('_')])

    def json(self):
        rtn = dict()
        for (k, v) in self.__dict__.items():
            if not k.startswith('_'):
                rtn[k] = v
        return rtn

#: used to populate help text via .format()
GLOBAL_OPTIONS = dict(
    registration_url='https://cdc.crossbar.io',
    credentials_path='~/.cdc/credentials',
    web_ui_url='https://cnet.crossbar.io/ops'
)


@inlineCallbacks
def connect(reactor, cfg):
    extra = {
        'verbose': cfg.verbose,
        'user': cfg.user,
        'key': cfg.key,
        'on_join': Deferred(),
    }

    runner = ApplicationRunner(
        url=cfg.router,
        realm=cfg.realm,
        extra=extra,
#        debug_wamp=cfg.debug,
#        debug=cfg.debug,
#        debug_app=cfg.debug,
    )
    yield runner.run(CdcSession, start_reactor=False)
    try:
        session, details = yield extra['on_join']
    except Exception as e:
        #raise click.ClickException("Failed to connect: {}".format(e.message))
        raise SystemExit("Failed to connect: {}".format(e.message))
    returnValue(session)


@click.group(help=
    click.style("{:^48}".format("Crossbar.io DevOps Center CLI"), bg='black', fg='yellow', bold=True) +
    """

    The 'cdc' command-line client connects to the Crossbar.io DevOps
    Center ("CDC") using a secure WAMP-over-Websockets connection and your
    credentials. This requires internet access from the machine you run
    'cdc' on.

    {registration_title}

    If you have not yet registered, you should visit {registration_url}

    cdc needs to be able to find your credentials via '{credentials_path}'
    or command-line options or environment variables.

    {activation_title}

    'cdc info' will show all nodes you have connected. To connect a node:

    If you have a current configuration, run 'crossbar activate' in
    the directory you'd normally run 'crossbar start' in.

    Otherwise, run 'crossbar init --cdc' in a fresh, empty directory
    to create a new crossbar node.

    All commands have a '--help' otion which prints their usage and exits.
     """.format(
         registration_title=click.style('Registration', bold=True, underline=True),
         activation_title=click.style('Creating a Node', bold=True, underline=True),
         **GLOBAL_OPTIONS
     )
)
@click.option(
    '--debug', '-d', 'debug', flag_value=True,
    default=False,
    help="Enable debug logging.",
)
@click.option(
    '--verbose', '-v', 'verbose', flag_value=True,
    default=False,
    help='More detailed output.',
)
@click.option(
    '--profile', default='default', envvar='CDC_PROFILE',
    help='The CDC user profile to use.',
)
@click.option(
    '--json', default=False,
    is_flag=True,
    help='Output in json instead of text',
)
@click.option(
    '--router', envvar='CDC_ROUTER', default=None,
    help="Override the router (cdc_router in profile)",
    metavar='URI',
)
@click.option(
    '--realm', envvar='CDC_REALM', default=None,
    help="Override the realm (cdc_realm in profile)",
)
@click.option(
    '--user', envvar='CDC_USER', default=None,
    help="Override the user (cdc_user in profile)",
    metavar='NAME',
)
@click.option(
    '--key', envvar='CDC_KEY', default=None,
    help="Override the key (cdc_key in profile)",
    metavar='BASE64',
)
@click.pass_context
def cdc(ctx, debug, verbose, profile, json, router, realm, user, key):
    cfg = Config()
    cfg.debug = debug
    cfg.verbose = verbose
    cfg.profile = profile
    cfg.output = 'json' if json else 'text'

    if verbose:
        click.echo('Using profile "{}"'.format(profile))

#    if json and verbose:
#        raise click.UsageError("Can't do verbose JSON output.")

    # set credentials defaults
    cfg.router = "wss://devops.crossbar.io/ws"

    # set credentials from configuration file
    cred_config = dict()
    credentials_filename = expanduser("~/.cdc/credentials")
    if os.path.exists(credentials_filename):
        config = ConfigParser.ConfigParser()
        config.read(credentials_filename)
        if profile in config.sections():
            if verbose:
                click.echo("Reading credentials for profile '{}' from '{}'".format(profile, credentials_filename))
            for k, v in config.items(profile):
                k = k.lower()
                if k in ['cdc_router', 'cdc_realm', 'cdc_user', 'cdc_key']:
                    cred_config[k[4:]] = v
        else:
            raise click.UsageError("profile '{}' not found in '{}'".format(profile, credentials_filename))
    else:
        raise click.UsageError("credentials file '{}' not found".format(credentials_filename))

    # only take things from credentials file if we didn't get a
    # command-line option (or env-var)
    for k in ['router', 'realm', 'user', 'key']:
        if locals()[k] is None:
            try:
                setattr(cfg, k, six.u(cred_config[k]))
            except KeyError:
                raise click.UsageError(
                    "Must specify {key} (via: --{key}, cdc_{key}= in "
                    "~/.cdc/credentials or CDC_{upper_key} env-var)".format(key=k, upper_key=k.upper())
                )
        else:
            setattr(cfg, k, locals()[k])
            if verbose and k in cred_config:
                click.echo("Overriding cdc_{key} with '{value}'".format(key=k, value=cred_config[k]))

    if verbose:
        if json:
            click.echo(pprint_json(cfg.json()))
        else:
            click.echo(repr(cfg))

    # remember parameters in CLI context
    ctx.obj = cfg


@cdc.command()
@click.argument('worker_id', metavar='WORKER_ID', required=True)
@click.option(
    '--list', '-L', 'list_profilers', default=None, flag_value=True,
    help='List available profilers',
)
@click.option(
    '--run-time', '-t', default=None,
    help='Seconds to run the profiler'
)
@click.pass_obj
def profile(cfg, worker_id, list_profilers, run_time):
    """
    Start a profiler against a running worker.
    """

    try:
        node_id, worker_id = worker_id.split('.')
    except ValueError:
        raise click.ClickException("Need the ID for a worker like 'node04.worker1'")

    @inlineCallbacks
    def run(reactor):
        session = yield connect(reactor, cfg)
        nodes = yield session.call(u"io.crossbar.cdc.list_nodes")
        if node_id not in [node['id'] for node in nodes]:
            click.echo("Node '{}' not found".format(node_id))
            raise SystemExit(1)
        workers = yield session.call(u"io.crossbar.cdc.list_workers", node_id)
        if not worker_id in [worker['id'] for worker in workers]:
            click.echo("Worker '{}' not found in node '{}'".format(worker_id, node_id))
            raise SystemExit(1)

        if list_profilers:
            click.echo("Available profilers for '{}.{}':".format(node_id, worker_id))
            profilers = yield session.call(u"io.crossbar.cdc.list_profilers", node_id, worker_id)
            for profiler in profilers:
                click.echo("  {}: state='{}'".format(profiler['id'], profiler['state']))
            return

        timestr = ''
        if run_time:
            timestr = ' (running for {}s)'.format(run_time)
        click.echo("Profiling '{}' in node '{}'{}.".format(worker_id, node_id, timestr))
        profile = yield session.call(
            u'io.crossbar.cdc.profile_worker', node_id, worker_id,
            run_time=run_time
        )
        # print("result:", profile)
        print_vmprof(profile)
    react(run)



@cdc.command()
@click.argument('node_id', metavar='NODE_ID', required=True)
@click.option(
    '--delete-config', flag_value=True, default=False,
    help="Remove all local configuration except the management uplink transport (XXX or just always rely on ignore it? or something else?)",
)
@click.option(
    '--no-uplink', flag_value=True, default=False,
    help="Do not add configuration for a management API connection to the CDC (XXX or just no option?)",
)
@click.option(
    '--config', '-C', 'config_dir', default='./.crossbar/',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="A directory containing crossbar.io configuration",
    show_default=True,
)
@click.option(
    '--overwrite', flag_value=True, default=False,
    help="Replace any existing config",
)
@click.option(
    '--force', flag_value=True, default=False,
    help="Continue even if there's already a management config",
)
@click.pass_obj
def activate(cfg, node_id, delete_config, no_uplink, config_dir, overwrite, force):
    """Run in a directory containing a .crossbar configuration directory
    and pass a NODE_ID argument, a unique name which is used to refer to this
    node in other commands (and the API).

    This will cause all the node's configuration to be sent to the CDC
    so that you may use other 'cdc' commands (or the Web UI, or the
    WAMP API) to control and monitor all aspects of this node's
    operation.

    NOTE: if you do not yet have a local crossbar.io configuration,
    you can instead use 'cdc create_node'

    """

    config_file = join(config_dir, 'config.json')
    if not exists(config_file):
        config_file = join(config_dir, 'config.yaml')
        if not exists(config_file):
            raise click.UsageError("Neither '{}' nor '{}' found.".format(
                click.format_filename(config_file),
                click.format_filename(join(config_dir, 'config.json')),
            ))
        import yaml
        config = yaml.load(open(config_file, 'r'))
    config = json.load(open(config_file, 'r'))

    if 'controller' in config:
        if 'manager' in config['controller'] and not force:
            click.echo(pprint_json(config['controller']['manager']))
            click.echo(click.style('Error:', fg='red') +
                       'There is already a management uplink configured for this node.')
            click.echo('If you are sure you want to over-write this information, use '
                       '--force or delete the configuration first.')
            raise click.ClickException("Aborting")

    cdc_dir = join(config_dir, '.cdc')
#    for cdc_file in [join(cdc_dir, 'node.key'), join(cdc_dir, 'node.id')]:
    for cdc_file in [join(cdc_dir, 'node.id')]:
        if exists(cdc_file) and not force:
            click.echo(
                click.style('Error:', fg='red') +
                (' Already have "{}"; if you are sure you '
                 'want to overwrite this information pass '
                 '--force or delete the file').format(cdc_file)
            )
            raise click.ClickException("Aborting")

    @inlineCallbacks
    def run(reactor):
        session = yield connect(reactor, cfg)

        click.echo("Sending config to the CDC...")
        try:
            response = yield session.call(u'io.crossbar.cdc.create_node', node_id, config, overwrite=overwrite)
            click.echo(response['message'])
            if 'key' not in response:
                raise click.ClickException("Expected 'key' in response")

            if no_uplink:
                click.echo("Not adding 'controller' configuration to '{}'".format(click.format_filename(config_file)))
                click.echo("The URL-safe BASE64 encoding of your private key is:")
                click.echo("")
                click.echo("   {}".format(response['key']))
                click.echo("")

            else:
                click.echo("{}: adding 'controller' config".format(click.format_filename(config_file)))

                # XXX looks like we "should" be using node.key,
                # presumably as the cryptosign key? For now, it's all
                # set up with wamp-cra, but we need to put these files
                # in place for now.
                node_fname = join(cdc_dir, "node.id")
                with open(node_fname, 'w') as f:
                    f.write(
                        '{node_id}@{realm}\n'.format(
                            node_id=node_id,
                            realm=cfg.realm,
                        )
                    )
                if cfg.verbose:
                    click.echo('Wrote "{}".'.format(node_fname))

                # XXX on the server side, need to use node.key as
                # cryptosign secret I guess, instead of wamp-cra.
                if False:
                    key_fname = join(cdc_dir, "node.key")
                    with open(key_fname, 'w') as f:
                        raw_key = urlsafe_b64decode(response['key'])
                        f.write(hexlify(raw_key))
                    if cfg.verbose:
                        click.echo(
                            'Wrote "{}" {}'.format(
                                key_fname,
                                click.style("contains secret-key material", fg=red),
                            )
                        )

                # XXX probably want to *not* burn in the transport here,
                # and therefore get the default CDC thing burned into
                # crossbar...? But: this makes testing easier
                isSecure, host, port, resource, path, params = parse_url(cfg.router)
                config["controller"] = {
                    "id": node_id,
                    "cdc": {
                        "enabled": True,
                        "realm": cfg.realm, # XXX redundant w/ node@realm thing in node.id?
                        "secret": response['key'],  # XXX redundant w/ node.key?
                        "transport": {
                            "type": "websocket",
                            "url": cfg.router,
                            "endpoint": {
                                "type": "tcp",
                                "host": host,
                                "port": port
                            }
                        }
                    }
                }

                # XXX for now: *removing* all the 'other' config
                # because currently crossbar's startup tries to do
                # both (e.g. the configured stuff AND connecting to
                # CDC).
                if True:# delete_config:
                    click.echo("Removing all config except management uplink")
                    for key in config.keys():
                        if key not in ['controller', 'version']:
                            del config[key]

                # XXX should probably "mv" the old file to
                # "config.json.backup" or something to be nice

                # XXX should probably write to TMP and the re-name
                # over top of "real" config-file (otherwise we make a
                # zero-length file if anything goes wrong dumping the
                # json/yaml)
                with open(config_file, 'w') as f:
                    if config_file.endswith('json'):
                        json.dump(config, f, indent=4)
                    else:
                        yaml.dump(config, f, indent=4)

                click.echo(
                    click.style('Alert', fg='red', bold=True) + ': ' +
                    click.style("'{}' now contains a secret key!".format(
                        config_file), fg='yellow', bold=True)
                )
                click.echo(
                    click.wrap_text(
                        "This file should be kept confidential. The key authenticates "
                        "this node to the Crossbar DevOps Center."
                    )
                )


        except ApplicationError as e:
            click.echo('{}: {}'.format(e.error, '\n'.join(e.args)))
            raise SystemExit(1)
        except Exception as e:
            click.echo('Error: {}'.format(e))
            raise SystemExit(1)
    react(run)


@cdc.command()
@click.pass_obj
def version(cfg):
    if cfg.output == 'text':
        print("CDC CLI version: {}".format(__version__))
    elif cfg.output == 'json':
        pprint_json({'version': __version__})
    else:
        raise Exception("logic error")


# XXX not really sure about this (especially the help-text), but at
# least don't have to copy-paste the same config around to use the
# same argument on many commands...
def id_spec_arg():
    return click.argument(
        'detail',
        default='',
        required=False,
        metavar='ID_SPEC',
    )
id_spec_help = """

ID_SPEC is a dot-separated filter that specifies a sub-tree to show
information about. Objects in the system are a hierarchy, with nodes
at the top level. A filter of nothing means to show everything.

Some example node specs: "node0.container0" (all container0's workers)
or "node0.router0.worker0" (just router0's worker0) or "..transport2"
for any transport called "transport2"
"""


@inlineCallbacks
def _get_all_node_info(reactor, session):
    """
    Returns JSON -style data for all nodes/transports/workers.

    XXX could do filtering, if configured, in here to avoid collecting
    too much information?
    """
    rtn = {}
    nodes = yield session.call(u"io.crossbar.cdc.list_nodes")
    for node in nodes:
        workers = yield session.call(u"io.crossbar.cdc.list_workers", node['id'])
        node['workers'] = workers or []
        for worker in workers:
            transports = None
            components = None
            if worker['type'] == 'router':
                transports = yield session.call(u"io.crossbar.cdc.list_transports", node['id'], worker['id'])
            elif worker['type'] == 'container':
                components = yield session.call(u"io.crossbar.cdc.list_components", node['id'], worker['id'])
            worker['transports'] = transports or []
            worker['components'] = components or []
        rtn[node['id']] = node
    returnValue(rtn)


def _filter_node_info(node_info, parts, cfg):
    """
    Filters out nodes/workers/{transports/components} according to 'parts'.
    """
    # filtering; could do in get_node_info instead?

    found_value = [False] * len(parts)
    nodes = dict()
    for node in node_info.values():
        if len(parts) > 0 and parts[0] and parts[0] != node['id']:
            if cfg.verbose:
                click.echo('skipping {}'.format(node['id']))
            continue

        nodes[node['id']] = node
        if len(parts) > 0:
            found_value[0] = True
        workers = []
        for worker in node['workers']:
            if len(parts) > 1 and parts[1] and parts[1] != worker['id']:
                if cfg.verbose:
                    click.echo('skipping {}'.format(worker['id']))
                continue

            workers.append(worker)
            if len(parts) > 1:
                found_value[1] = True

            transports = []
            for transport in worker['transports']:
                if len(parts) > 2 and parts[2] and parts[2] != transport['id']:
                    if cfg.verbose:
                        click.echo('skipping {}'.format(transport['id']))
                    continue
                transports.append(transport)
                if len(parts) > 2:
                    found_value[2] = True
            worker['transports'] = transports

            components = []
            for component in worker['components']:
                if len(parts) > 2 and parts[2] and parts[2] != component['id']:
                    if cfg.verbose:
                        click.echo('skipping {}'.format(component['id']))
                    continue
                components.append(component)
                if len(parts) > 2:
                    found_value[2] = True
            worker['components'] = components
        node['workers'] = workers

    if not all(found_value):
        for (found, part) in zip(found_value, parts):
            if not found and part:
                unfound = parts[found_value.index(False)]
                raise click.UsageError("Didn't find '{}' for ID_SPEC '{}'".format(unfound, '.'.join(parts)))
    return nodes


def _wrap_and_indent(text, indent='    '):
    """
    Internal helper. Wraps and indents text (default is 4
    spaces). Should be used for all helpful-text we display.
    """
    wrapper = TextWrapper(
        width=80,
        initial_indent=indent,
        subsequent_indent=indent,
    )
    return wrapper.fill(text)


def wamp_error_handler(fn):
    @wraps(fn)
    def wrapper(*args, **kw):
        d = fn(*args, **kw)

        def trap_wamp(fail):
            fail.trap(ApplicationError)
            error = click.style(fail.value.error, fg='red')
            click.echo("{}: {}".format(error, fail.value.message))
            click.echo(
                _wrap_and_indent(
                    "It's likely this client is out of date or there is a problem "
                    "with the Crossbar Devop Center (CDC)."
                )
            )
            raise SystemExit(10)
        d.addErrback(trap_wamp)
        return d
    return wrapper

@cdc.command(help="Get information about one or many objects." + id_spec_help)
@id_spec_arg()
@click.option(
    '--absolute', flag_value=True, default=False,
    help="Show timestamps etc in absolute values.",
)
@click.pass_obj
def info(cfg, detail, absolute):
    parts = detail.split('.')

    @wamp_error_handler
    @inlineCallbacks
    def run(reactor):
        session = yield connect(reactor, cfg)

        node_info = yield _get_all_node_info(reactor, session)
        node_info = _filter_node_info(node_info, parts, cfg)

        # short-circuit with json data
        if cfg.output == 'json':
            pprint_json(node_info)
            return

        # render the json we have as text. colour-configuration?

        # XXX --absolute option to skip doing the humanize stuff? (can
        # always get in json, though, if you want the real timestamp
        # strings)

        msg = ("{:^50}").format("Management realm '{}'".format(session.config.realm))
        click.echo(click.style(msg, bg=HIGHLIGHT_BG, fg=HIGHLIGHT_FG, bold=True), nl=True)

        now = datetime.utcnow()

        for node in node_info.values():
            if absolute:
                started_ago = "started {}".format(node['started'])
            else:
                started_ago = now - datetime.strptime(node['started'].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                started_ago = "started {} ago".format(humanize.naturaldelta(started_ago))
            click.echo(click.style(node['id'], bold=True), nl=False)
            click.echo(": ({started_ago})".format(
                started_ago=started_ago,
                **node)
            )

            for worker in node['workers']:
                fg = 'red'
                if worker['status'] == 'started':
                    fg = 'green'
                click.echo('  ' + click.style(worker['id'], fg=fg), nl=False)
                if absolute:
                    nice_uptime = str(int(worker['uptime'])) + 's'
                else:
                    nice_uptime = humanize.naturaldelta(worker['uptime'])
                click.echo(" ({type}): up {nice_uptime}, pid={pid}".format(nice_uptime=nice_uptime, **worker))

                try:
                    stats = yield session.call(u'io.crossbar.cdc.get_stats', node['id'], worker['id'])
                    nice_resident = '{} resident'.format(humanize.naturalsize(stats['stats']['resident']))
                    click.echo("    {nice_resident}".format(nice_resident=nice_resident, **stats))
                except Exception as e:
                    click.echo("    stats: " + click.style("error", fg='red'))

                for transport in worker['transports']:
                    if absolute:
                        created_ago = "created {}".format(transport['created'])
                    else:
                        created_ago = now - datetime.strptime(transport['created'].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                        created_ago = "created {} ago".format(humanize.naturaldelta(created_ago))
                    endpoint_detail = ''
                    ep = transport['config']['endpoint']
                    if ep['type'] == 'tcp':
                        host = ep['host'] if 'host' in ep else '127.0.0.1'
                        endpoint_detail = '{host}:{port}'.format(host=host, **ep)
                    elif ep['type'] == 'unix':
                        endpoint_detail = ep['path']
                    print("    {id}: {config[type]}/{config[endpoint][type]} ({ep}), {created_ago}".format(
                        created_ago=created_ago,
                        ep=endpoint_detail,
                        **transport
                    ))

                for component in worker['components']:
                    if absolute:
                        started_ago = "started {}".format(component['started'])
                    else:
                        started_ago = now - datetime.strptime(component['started'].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                        started_ago = "started {} ago".format(humanize.naturaldelta(started_ago))
                    detail = ''
                    if component['config']['type'] == 'class':
                        detail = click.style(component['config']['classname'], fg=HIGHLIGHT_FG)
                    elif component['config']['type'] == 'wamplet':
                        detail = '{}[{}]'.format(
                            click.style(component['config']['package'], fg=HIGHLIGHT_FG),
                            click.style(component['config']['entrypoint'], fg=HIGHLIGHT_FG),
                        )
                    print("    {id}: {detail} ({started_ago}, up {nice_uptime})".format(
                        started_ago=started_ago,
                        nice_uptime=humanize.naturaldelta(component['uptime']),
                        detail=detail,
                        **component
                    ))
    react(run)


@cdc.command()
@click.argument(
    'worker',
    default='',
    required=True,
    metavar='ID',
)
@click.pass_obj
def log(cfg, worker):
    """
    monitor active logs from a worker.

    A worker ID is "node_id.worker_id", e.g. node4.worker1
    """

    parts = worker.split('.')
    if len(parts) < 1 or len(parts) > 2:
        raise click.UsageError("worker ID must be 'node2.worker3' style")
    node_id = parts[0]
    worker_id = parts[1] if len(parts) > 1 else None

    @inlineCallbacks
    def monitor(reactor):
        session = yield connect(reactor, cfg)
        nodes = yield session.call(u"io.crossbar.cdc.list_nodes")
        if node_id not in [node['id'] for node in nodes]:
            raise Exception("Node '{}' not found".format(node_id))

        workers = yield session.call(u"io.crossbar.cdc.list_workers", node_id)
        if worker_id is not None:
            if worker_id not in [worker['id'] for worker in workers]:
                raise Exception("Worker '{}' not found in node '{}'".format(worker_id, node_id))
            workers = [worker_id]  # avoid special-casing the for loop below
        else:
            workers = [worker['id'] for worker in workers]

        import time
        def on_log(wid, line, details=None, **kw):
            ts = kw.get('log_time', 0)
            ts = time.asctime(time.gmtime(ts))
            wid = click.style(wid, fg='yellow')
            if kw.get('isError', False):
                click.echo('{}: {} {}'.format(wid, click.style(str(ts), fg='red'), line))
            else:
                click.echo('{}: {} {}'.format(wid, ts, line))

        calls = []
        for wid in workers:
            # uri = u'local.crossbar.node.{}.worker.{}.on_log'.format(node_id, wid)
            uri = u'io.crossbar.cdc.node.{}.worker.{}.on_log'.format(node_id, wid)
            yield session.subscribe(partial(on_log, wid), uri)

            # this re-sends all past log-events (obviously, this is a
            # perfect candidate for "event history" but ...)
            calls.append(session.call(u'io.crossbar.cdc.log_history', node_id, wid))

        yield DeferredList(calls)
        click.echo('{}: {} --- start monitoring new events (ctrl-c to end) ---'.format(
            node_id, click.style(time.asctime(time.gmtime()), fg='yellow')))

        yield Deferred()  # wait forever, e.g. ctrl-c
    react(monitor)


@inlineCallbacks
def _action_on_objects(reactor, cfg, verb, parts):
    """
    this would be shared by stop/start/etc as much as possible...
    """
    session = yield connect(reactor, cfg)

    # XXX probably would special-case 'create' since it's
    # ... special. stop/reload/start etc all work on existing objects.

    node_info = yield _get_all_node_info(reactor, session)
    node_info = _filter_node_info(node_info, parts, cfg)


    # node info contains the things we want to act on PLUS their
    # parents, so we must be careful e.g. not to stop a whole node if
    # a transport was specified...also we need to order things properly...

    level = len(parts)
    if level > 3:
        raise Exception("ID_SPEC is too long: {}".format(parts))
    # level 0 is nodes, level 1 is workers/guests/etc, level 2 is transprots/
    transports = []
    components = []
    workers = []
    nodes = []
    # note that we DO want to collect every single transport if we're
    # at level 0, 1 or 2 but only collect nodes if we're at level 0
    for node in node_info.values():
        if level <= 1:
            nodes.append(node)
        for worker in node['workers']:
            if level >= 2:
                workers.append((worker['type'], node['id'], worker['id']))
            for transport in worker['transports']:
                if level >= 3:
                    transports.append((node['id'], worker['id'], transport['id']))
            for component in worker['components']:
                if level >= 3:
                    components.append((node['id'], worker['id'], component['id']))

    @inlineCallbacks
    def call_with_args(url, *args):
        if cfg.verbose:
            click.echo('{url}({args}): '.format(url=url, args=', '.join(args)), nl=False)
        try:
            x = yield session.call(url, *args)
            if cfg.verbose:
                click.echo(str(x))
        except Exception as e:
            click.echo(click.style(e.message, fg='red'))

    for args in components:
        url = 'io.crossbar.cdc.{}_component'.format(verb)
        yield call_with_args(url, *args)
    for args in transports:
        url = 'io.crossbar.cdc.{}_transport'.format(verb)
        yield call_with_args(url, *args)
    for args in workers:
        url = 'io.crossbar.cdc.{}_{}'.format(verb, args[0])
        yield call_with_args(url, *args[1:])
    for node in nodes:
        url = 'io.crossbar.cdc.node.{}.{}'.format(node['id'], verb)
        yield call_with_args(url)

"""
    if verb == 'start':
        calls.reverse()
        urls.reverse()

    #results = yield DeferredList(calls, consumeErrors=True)
    #for result, call in zip(results, urls):
    for (call, url) in zip(calls, urls):
        click.echo("call: {}".format(url))
        res = yield call
        #ok, res = result
        url, args = call
        if not ok:
            click.echo(click.style(url, fg='red') + '({}): {}'.format(', '.join(map(repr, args[1:])), res.value.message))
        else:
            click.echo(click.style('.'.join(args[1:]), fg='green') + ': {}-ed'.format(verb))
"""


@cdc.command(help="Stop one or many objects." + id_spec_help)
@id_spec_arg()
@click.pass_obj
def stop(cfg, detail):
    """
    kind of demo-ing this here; would do very-simiar code for start/restart/ etcetc.
    """
    parts = detail.split('.')
    if not detail:
        raise click.ClickException("Not stopping everything on empty-string. Use 'cdc stop .'")

    react(_action_on_objects, (cfg, 'stop', parts))


@cdc.command(help="Stop one or many objects." + id_spec_help)
@id_spec_arg()
@click.pass_obj
def start(cfg, detail):
    """
    kind of demo-ing this here; would do very-simiar code for start/restart/ etcetc.
    """
    parts = detail.split('.')

    react(_action_on_objects, (cfg, 'start', parts))

@cdc.group()
def create():
    pass


_worker_help = """
Create a new router or container.

Valid keys/values in the --config dict are:

\b
title: process title
reactor: dict configuring reactor
python: path to python exe
pythonpath: list of paths
cpu_affinity: int
env: dict containing keys:
    inherit: bool
    vars: dict of environment variable names/values
"""

@create.command('router', help=_worker_help)
@click.argument(
    'name',
    required=True,
)
@click.option(
    '--config', '-c', 'configfile',
    type=click.File('rb'),
    default=six.StringIO('{}'),
    help="""JSON containing valid Native Worker options",
""",
)
@click.pass_obj
def create_router(cfg, name, configfile):
    return create_worker('router', cfg, name, configfile)


@create.command('container', help=_worker_help)
@click.argument(
    'name',
    required=True,
)
@click.option(
    '--config', '-c', 'configfile',
    type=click.File('rb'),
    default=six.StringIO('{}'),
    help="""JSON containing valid Native Worker options",
""",
)
@click.pass_obj
def create_container(cfg, name, configfile):
    return create_worker('container', cfg, name, configfile)


def create_worker(type_, cfg, name, configfile):
    parts = name.split('.')
    if len(parts) < 2:
        raise click.UsageError("Need to know which node; pass a name like 'node4.{}6'".format(type_))
    if len(parts) > 2:
        raise click.UsageError("A {} ID is simply '{}.{}'".format(type_, parts[0], parts[1]))

    node_id = parts[0]
    new_worker_id = parts[1]

    try:
        worker_config = json.load(configfile)
    except Exception as e:
        # invalid JSON or similar; can't continue
        raise click.ClickException('{}: {}'.format(configfile.name, e.message))

    @inlineCallbacks
    def run(reactor):
        session = yield connect(reactor, cfg)
        yield session.call(u"io.crossbar.cdc.create_{}".format(type_), node_id, new_worker_id, worker_config)
    react(run)


if __name__ == '__main__':
    cdc()
