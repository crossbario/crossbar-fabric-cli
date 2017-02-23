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

import sys
import time
import locale
import json
import asyncio
import click
from pygments import highlight, lexers, formatters
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import prompt, prompt_async
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from autobahn.util import utcnow
from crossbarfabriccli import client, repl


_HAS_COLOR_TERM = False
try:
    import colorama

    # https://github.com/tartley/colorama/issues/48
    term = None
    if sys.platform == 'win32' and 'TERM' in os.environ:
        term = os.environ.pop('TERM')

    colorama.init()
    _HAS_COLOR_TERM = True

    if term:
        os.environ['TERM'] = term

except ImportError:
    pass


def style_crossbar(text):
    if _HAS_COLOR_TERM:
        return click.style(text, fg='yellow', bold=True)
    else:
        return text


def style_finished_line(text):
    if _HAS_COLOR_TERM:
        return click.style(text, fg='yellow')
    else:
        return text


def localnow():
    return time.strftime(locale.nl_langinfo(locale.D_T_FMT), time.localtime())


class Application(object):

    OUTPUT_PLAIN = 'plain'
    OUTPUT_JSON = 'json'
    OUTPUT_JSON_COLORED = 'json-color'

    WELCOME = """
    Welcome to {title}!

    Press Ctrl-C to cancel the current command, and Ctrl-D to exit the shell.
    Type "help" to get help. Try TAB for auto-completion.

    """.format(title=style_crossbar('Crossbar.io Fabric Shell'))

    def __init__(self):
        self.current_resource_type = None
        self.current_resource = None
        self.session = None

        self._history = FileHistory('.cbsh-history')

        self._output = Application.OUTPUT_JSON_COLORED

        self._output_finished_verbose = False

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

    def format_selected(self):
        return u'{} -> {}.\n'.format(self.current_resource_type, self.current_resource)

    def print_selected(self):
        click.echo(self.format_selected())

    def selected(self):
        return self.current_resource_type, self.current_resource

    def __str__(self):
        return u'Application(current_resource_type={}, current_resource={})'.format(self.current_resource_type, self.current_resource)

    async def run_command(self, cmd):
        result = await cmd.run(self.session)

        if self._output in [Application.OUTPUT_JSON, Application.OUTPUT_JSON_COLORED]:

            json_str = json.dumps(result.result,
                                  separators=(', ', ': '),
                                  sort_keys=True,
                                  indent=4,
                                  ensure_ascii=False)

            if self._output == Application.OUTPUT_JSON_COLORED:
                console_str = highlight(json_str,
                                        lexers.JsonLexer(),
                                        formatters.TerminalFormatter())
            else:
                console_str = json_str

        click.echo(console_str)
        if self._output_finished_verbose:
            if result.duration:
                click.echo(style_finished_line(u'Finished in {} ms on {}.'.format(result.duration, localnow())))
            else:
                click.echo(style_finished_line(u'Finished successfully on {}.'.format(localnow())))
        else:
            if result.duration:
                click.echo(style_finished_line(u'Finished in {} ms.'.format(result.duration)))
            else:
                click.echo(style_finished_line(u'Finished successfully.'))

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
        click.echo(self.WELCOME)
        loop = asyncio.get_event_loop()

        self.session = client.run()

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
        loop.close()
