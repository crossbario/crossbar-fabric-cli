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
import socket
import json
import yaml
import asyncio
import click

import txaio
import sys
txaio.use_asyncio()

import pygments
from pygments import highlight, lexers, formatters

from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

from autobahn.websocket.util import parse_url
from autobahn.wamp.types import ComponentConfig
from autobahn.wamp.exception import ApplicationError
from autobahn.asyncio.wamp import ApplicationRunner

from crossbarfabricshell.util import (
    style_crossbar,
    style_finished_line,
    style_error,
    style_ok,
    localnow
)
from crossbarfabricshell import client, repl, config, key, __version__


_DEFAULT_CFC_URL = u'wss://fabric.crossbario.com'


class WebSocketURL(click.ParamType):
    """
    WebSocket URL validator.
    """

    name = 'WebSocket URL'

    def __init__(self):
        click.ParamType.__init__(self)

    def convert(self, value, param, ctx):
        try:
            parse_url(value)
        except Exception as e:
            self.fail(style_error(str(e)))
        else:
            return value


def _prompt_for_url():
    """
    Prompt user for CFC URL to create a new ~/.cbf/config.ini file
    """
    value = click.prompt('Crossbar.io Fabric Center URL', type=WebSocketURL(), default=_DEFAULT_CFC_URL)
    return value


# default configuration stored in $HOME/.cbf/config.ini
_DEFAULT_CONFIG = """[default]

url={url}
privkey=default.priv
pubkey=default.pub
"""


class Application(object):

    OUTPUT_FORMAT_PLAIN = 'plain'
    OUTPUT_FORMAT_JSON = 'json'
    OUTPUT_FORMAT_JSON_COLORED = 'json-color'
    OUTPUT_FORMAT_YAML = 'yaml'
    OUTPUT_FORMAT_YAML_COLORED = 'yaml-color'

    OUTPUT_FORMAT = [OUTPUT_FORMAT_PLAIN,
                     OUTPUT_FORMAT_JSON,
                     OUTPUT_FORMAT_JSON_COLORED,
                     OUTPUT_FORMAT_YAML,
                     OUTPUT_FORMAT_YAML_COLORED]

    OUTPUT_VERBOSITY_SILENT = 'silent'
    OUTPUT_VERBOSITY_RESULT_ONLY = 'result-only'
    OUTPUT_VERBOSITY_NORMAL = 'normal'
    OUTPUT_VERBOSITY_EXTENDED = 'extended'

    OUTPUT_VERBOSITY = [OUTPUT_VERBOSITY_SILENT,
                        OUTPUT_VERBOSITY_RESULT_ONLY,
                        OUTPUT_VERBOSITY_NORMAL,
                        OUTPUT_VERBOSITY_EXTENDED]

    # list of all available Pygments styles (including ones loaded from plugins)
    # https://www.complang.tuwien.ac.at/doc/python-pygments/styles.html
    OUTPUT_STYLE = list(pygments.styles.get_all_styles())

    WELCOME = """
    Welcome to {title} v{version}

    Press Ctrl-C to cancel the current command, and Ctrl-D to exit the shell.
    Type "help" to get help. Try TAB for auto-completion.
    """.format(title=style_crossbar('Crossbar.io Fabric Shell'), version=__version__)

    CONNECTED = """    Connection:

        url         : {url}
        authmethod  : {authmethod}
        realm       : {realm}
        authid      : {authid}
        authrole    : {authrole}
        session     : {session}
    """

    def __init__(self):
        self.current_resource_type = None
        self.current_resource = None
        self.session = None
        self._history = FileHistory('.cbsh-history')
        self._output_format = Application.OUTPUT_FORMAT_JSON_COLORED
        self._output_verbosity = Application.OUTPUT_VERBOSITY_NORMAL

        self._style = style_from_dict({
            Token.Toolbar: '#fce94f bg:#333333',

            # User input.
            #Token:          '#ff0066',

            # Prompt.
            #Token.Username: '#884444',
            #Token.At:       '#00aa00',
            #Token.Colon:    '#00aa00',
            #Token.Pound:    '#00aa00',
            #Token.Host:     '#000088 bg:#aaaaff',
            #Token.Path:     '#884444 underline',
        })

        self._output_style = 'fruity'

    def _load_profile(self, dotdir=None, profile=None):

        dotdir = dotdir or u'~/.cbf'
        profile = profile or u'default'

        cbf_dir = os.path.expanduser(dotdir)
        if not os.path.isdir(cbf_dir):
            os.mkdir(cbf_dir)
            click.echo(u'Created new local user directory: {}'.format(style_ok(cbf_dir)))

        config_path = os.path.join(cbf_dir, 'config.ini')
        if not os.path.isfile(config_path):
            with open(config_path, 'w') as f:
                url = _prompt_for_url()
                f.write(_DEFAULT_CONFIG.format(url=url))
            click.echo(u'Created new local user configuration: {}'.format(style_ok(config_path)))

        config_obj = config.UserConfig(config_path)

        profile_obj = config_obj.profiles.get(profile, None)
        if not profile_obj:
            raise click.ClickException('no such profile: "{}"'.format(profile))
        else:
            click.echo('Active user profile: {}'.format(style_ok(profile)))

        privkey_path = os.path.join(cbf_dir, profile_obj.privkey or u'{}.priv'.format(profile))
        pubkey_path = os.path.join(cbf_dir, profile_obj.pubkey or u'default.pub')
        key_obj = key.UserKey(privkey_path, pubkey_path)

        return key_obj, profile_obj

    def set_output_format(self, output_format):
        """
        Set command output format.

        :param output_format: The verbosity to use.
        :type output_format: str
        """
        if output_format in Application.OUTPUT_FORMAT:
            self._output_format = output_format
        else:
            raise Exception('invalid value {} for output_format (not in {})'.format(output_format, Application.OUTPUT_FORMAT))

    def set_output_verbosity(self, output_verbosity):
        """
        Set command output verbosity.

        :param output_verbosity: The verbosity to use.
        :type output_verbosity: str
        """
        if output_verbosity in Application.OUTPUT_VERBOSITY:
            self._output_verbosity = output_verbosity
        else:
            raise Exception('invalid value {} for output_verbosity (not in {})'.format(output_verbosity, Application.OUTPUT_VERBOSITY))

    def set_output_style(self, output_style):
        """
        Set pygments syntax highlighting style ("theme") to be used for command result output.

        :param output_style: The style to use.
        :type output_style: str
        """
        if output_style in Application.OUTPUT_STYLE:
            self._output_style = output_style
        else:
            raise Exception('invalid value {} for output_style (not in {})'.format(output_style, Application.OUTPUT_STYLE))

    def error(self, msg):
        click.echo()

    def format_selected(self):
        return u'{} -> {}.\n'.format(self.current_resource_type, self.current_resource)

    def print_selected(self):
        click.echo(self.format_selected())

    def selected(self):
        return self.current_resource_type, self.current_resource

    def __str__(self):
        return u'Application(current_resource_type={}, current_resource={})'.format(self.current_resource_type, self.current_resource)

    async def run_command(self, cmd):
        try:
            result = await cmd.run(self.session)
        except Exception as e:
            print(e)

        if self._output_format in [Application.OUTPUT_FORMAT_JSON, Application.OUTPUT_FORMAT_JSON_COLORED]:

            json_str = json.dumps(result.result,
                                  separators=(', ', ': '),
                                  sort_keys=True,
                                  indent=4,
                                  ensure_ascii=False)

            if self._output_format == Application.OUTPUT_FORMAT_JSON_COLORED:
                console_str = highlight(json_str,
                                        lexers.JsonLexer(),
                                        formatters.Terminal256Formatter(style=self._output_style))
            else:
                console_str = json_str

        elif self._output_format in [Application.OUTPUT_FORMAT_YAML, Application.OUTPUT_FORMAT_YAML_COLORED]:

            yaml_str = yaml.safe_dump(result.result)

            if self._output_format == Application.OUTPUT_FORMAT_YAML_COLORED:
                console_str = highlight(yaml_str,
                                        lexers.YamlLexer(),
                                        formatters.Terminal256Formatter(style=self._output_style))
            else:
                console_str = yaml_str

        elif self._output_format == Application.OUTPUT_FORMAT_PLAIN:

            #console_str = u'{}'.format(pprint.pformat(result.result))
            console_str = u'{}'.format(result)

        else:
            # should not arrive here
            raise Exception('internal error: unprocessed value "{}" for output format'.format(self._output_format))

        # output command metadata (such as runtime)
        if self._output_verbosity == Application.OUTPUT_VERBOSITY_SILENT:
            pass
        else:
            # output result of command
            click.echo(console_str)

            if self._output_verbosity == Application.OUTPUT_VERBOSITY_RESULT_ONLY or self._output_format == Application.OUTPUT_FORMAT_PLAIN:
                pass
            elif self._output_verbosity == Application.OUTPUT_VERBOSITY_NORMAL:
                if result.duration:
                    click.echo(style_finished_line(u'Finished in {} ms.'.format(result.duration)))
                else:
                    click.echo(style_finished_line(u'Finished successfully.'))
            elif self._output_verbosity == Application.OUTPUT_VERBOSITY_EXTENDED:
                if result.duration:
                    click.echo(style_finished_line(u'Finished in {} ms on {}.'.format(result.duration, localnow())))
                else:
                    click.echo(style_finished_line(u'Finished successfully on {}.'.format(localnow())))
            else:
                # should not arrive here
                raise Exception('internal error')

    def _get_bottom_toolbar_tokens(self, cli):
        toolbar_str = ' Current resource path: {}'.format(self.format_selected())
        return [
            (Token.Toolbar, toolbar_str),
        ]

    def _get_prompt_tokens(self, cli):
        return [
            (Token.Username, 'john'),
            (Token.At,       '@'),
            (Token.Host,     'localhost'),
            (Token.Colon,    ':'),
            (Token.Path,     '/user/john'),
            (Token.Pound,    '# '),
        ]

    def run_context(self, ctx):

        if False:
            click.echo('Logging started ..')
            txaio.start_logging(level='debug', out=sys.stdout)

        # cfg contains the command lines options and arguments that
        # click collected for us
        cfg = ctx.obj

        cmd = ctx.command.name
        if cmd not in [u'auth', u'shell']:
            raise click.ClickException('"{}" command can only be run in shell'.format(cmd))

        click.echo('Crossbar.io Fabric Shell: {}'.format(style_ok('v{}'.format(__version__))))

        # load user profile and key for given profile name
        key, profile = self._load_profile(profile=cfg.profile)

        # set the Fabric URL to connect to from the profile or default
        url = profile.url or u'wss://fabric.crossbario.com'

        # users always authenticate with the user_id from the key, which
        # filled from the email the user provided
        authid = key.user_id

        # the realm can be set from command line, env var, the profile
        # or can be None, which means the user will be joined to the global
        # Crossbar.io Fabric users realm (u'com.crossbario.fabric')
        realm = cfg.realm or profile.realm or None

        # the authrole can be set from command line, env var, the profile
        # or can be None, in which case the role is chosen automatically
        # from the list of roles the user us authorized for
        authrole = cfg.role or profile.role or None

        # this will be fired when the ShellClient below actually has joined
        # the respective realm on Crossbar.io Fabric (either the global users
        # realm, or a management realm the user has a role on)
        ready = asyncio.Future()

        extra = {
            # these are forward on the actual client connection
            u'authid': authid,
            u'authrole': authrole,

            # these are native Python object and only used client-side
            u'key': key.key,
            u'done': ready
        }

        # for the "auth" command, forward additional command line options
        if ctx.command.name == u'auth':
            # user provides authentication code to verify
            extra[u'activation_code'] = cfg.code

            # user requests sending of a new authentication code (while an old one is still pending)
            extra[u'request_new_activation_code'] = cfg.new_code

        # this is the WAMP ApplicationSession that connects the CLI to Crossbar.io Fabric
        self.session = client.ShellClient(ComponentConfig(realm, extra))

        loop = asyncio.get_event_loop()
        runner = ApplicationRunner(url, realm)

        # this might fail eg when the transport connection cannot be established
        try:
            click.echo('Connecting to {} ..'.format(url))
            _res = runner.run(self.session, start_loop=False)
        except socket.gaierror as e:
            click.echo(style_error('Could not connect to {}: {}'.format(url, e)))
            loop.close()
            sys.exit(1)

        exit_code = 0
        try:
            # "connected" will complete when the WAMP session to Fabric
            # has been established and is ready
            click.echo('Entering event loop ..')
            transport, protocol = loop.run_until_complete(_res)
            #click.echo('transport, protocol: {} {}'.format(transport, protocol))
            #loop.run_forever()
            session_details = loop.run_until_complete(ready)
            #click.echo('SessionDetails: {}'.format(session_details))

        except ApplicationError as e:

            # some ApplicationErrors are actually signaling progress
            # in the authentication flow, some are real errors

            if e.error.startswith(u'fabric.auth-failed.'):
                error = e.error.split(u'.')[2]
                message = e.args[0]

                if error == u'new-user-auth-code-sent':

                    click.echo('\nThanks for registering! {}'.format(message))
                    click.echo(style_ok('Please check your inbox and run "cbsh auth --code <THE CODE YOU GOT BY EMAIL>.\n'))

                elif error == u'registered-user-auth-code-sent':

                    click.echo('\nWelcome back! {}'.format(message))
                    click.echo(style_ok('Please check your inbox and run "cbsh auth --code <THE CODE YOU GOT BY EMAIL>.\n'))

                elif error == u'pending-activation':

                    click.echo()
                    click.echo(style_ok(message))
                    click.echo()
                    click.echo('Tip: to activate, run "cbsh auth --code <THE CODE YOU GOT BY EMAIL>"')
                    click.echo('Tip: you can request sending a new code with "cbsh auth --new-code"')
                    click.echo()

                elif error == u'no-pending-activation':

                    exit_code = 1
                    click.echo()
                    click.echo(style_error('{} [{}]'.format(message, e.error)))
                    click.echo()

                elif error == u'email-failure':

                    exit_code = 1
                    click.echo()
                    click.echo(style_error('{} [{}]'.format(message, e.error)))
                    click.echo()

                elif error == u'invalid-activation-code':

                    exit_code = 1
                    click.echo()
                    click.echo(style_error('{} [{}]'.format(message, e.error)))
                    click.echo()

                else:

                    # we should not arrive here! otherwise, add a new clause above and handle the situation
                    exit_code = 1
                    click.echo(style_error('Internal error: unprocessed error type {}:'.format(error)))
                    click.echo(style_error(message))

            elif e.error.startswith(u'crossbar.error.'):

                error = e.error.split(u'.')[2]
                message = e.args[0]

                if error == u'invalid_configuration':

                    click.echo()
                    click.echo(style_error('{} [{}]'.format(message, e.error)))
                    click.echo()
                else:

                    # we should not arrive here! otherwise, add a new clause above and handle the situation
                    exit_code = 1
                    click.echo(style_error('Internal error: unprocessed error type {}:'.format(error)))
                    click.echo(style_error(message))

            else:

                click.echo(style_error('{}'.format(e)))
                exit_code = 1
                raise

        else:

            if cmd == u'auth':

                self._print_welcome(url, session_details)

            elif cmd == 'shell':

                click.clear()
                try:
                    self._print_welcome(url, session_details)
                except Exception as e:
                    click.echo('err: {}'.format(e))

                prompt_kwargs = {
                    'history': self._history,
                }

                shell_task = loop.create_task(
                    repl.repl(ctx,
                              get_bottom_toolbar_tokens=self._get_bottom_toolbar_tokens,
                              #get_prompt_tokens=self._get_prompt_tokens,
                              style=self._style,
                              prompt_kwargs=prompt_kwargs)
                )

                loop.run_until_complete(shell_task)

            else:
                # should not arrive here, as we checked cmd in the beginning
                raise Exception('logic error')

        finally:
            loop.close()
            sys.exit(exit_code)

    def _print_welcome(self, url, session_details):
        click.echo(self.WELCOME)
        click.echo(self.CONNECTED.format(
            url=url,
            realm=style_crossbar(session_details.realm) if session_details else None,
            authmethod=session_details.authmethod if session_details else None,
            authid=style_crossbar(session_details.authid) if session_details else None,
            authrole=style_crossbar(session_details.authrole) if session_details else None,
            session=session_details.session if session_details else None
            ))
