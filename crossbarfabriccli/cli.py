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

import asyncio
import click
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import prompt, prompt_async
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from crossbarfabriccli import client, repl, command


WELCOME = """
Welcome to Crossbar.io Fabric Shell!

Press Ctrl-C to cancel the current command, and Ctrl-D to exit the shell.
Type "help" to get help. Try TAB for auto-completion.

"""

USAGE = """
Examples:
To start the interactive shell, use the "shell" command:

    cbf shell

You can run the shell under different user profile
using the "--profile" option:

    cbf --profile mister-test1 shell
"""


class Application(object):

    def __init__(self):
        self.current_resource_type = None
        self.current_resource = None
        self.session = None

    def get_bottom_toolbar_tokens(self, cli):
            return [(Token.Toolbar, 'current resource: {}'.format(self.format_selected()))]

    def format_selected(self):
        return u'{} -> {}.\n'.format(self.current_resource_type, self.current_resource)

    def print_selected(self):
        click.echo(self.format_selected())

    def selected(self):
        return self.current_resource_type, self.current_resource

    def __str__(self):
        return u'Application(current_resource_type={}, current_resource={})'.format(self.current_resource_type, self.current_resource)

_app = Application()


class Config(object):

    def __init__(self, app, profile):
        self.app = app
        self.profile = profile
        self.verbose = None
        self.resource_type = None
        self.resource = None

    def __str__(self):
        return u'Config(verbose={}, resource_type={}, resource={})'.format(self.verbose, self.resource_type, self.resource)


async def run_command(cmd, session):
    result = await cmd.run(session)
    click.echo(result)


def run_context(ctx):
    click.echo(WELCOME)
    loop = asyncio.get_event_loop()

    app = ctx.obj.app

    app.session = client.run()

    prompt_kwargs = {
        'history': FileHistory('cbf-history'),
    }

    shell_task = loop.create_task(
        repl.repl(ctx,
                  get_bottom_toolbar_tokens=app.get_bottom_toolbar_tokens,
                  prompt_kwargs=prompt_kwargs)
    )

    loop.run_until_complete(shell_task)
    loop.close()

# @click.group(invoke_without_command=True)
@click.group()
@click.option(
    '--profile',
    help='profile to use',
    default=u'default'
)
@click.pass_context
def cli(ctx, profile):
    ctx.obj = Config(_app, profile)


@cli.command(name='login', help='authenticate user profile / key-pair with Crossbar.io Fabric')
@click.pass_context
async def cmd_login(ctx):
    click.echo('authenticating profile "{}" ..'.format(ctx.obj.profile))


@cli.command(name='shell', help='run an interactive Crossbar.io Fabric shell')
@click.pass_context
def cmd_shell(ctx):
    run_context(ctx)


@cli.command(name='clear', help='clear screen')
async def cmd_clear():
    click.clear()


@cli.command(name='help', help='general help')
@click.pass_context
async def cmd_help(ctx):
    click.echo(ctx.parent.get_help())
    click.echo(USAGE)


@cli.group(name='list', help='list resources')
@click.option(
    '--verbose',
    help='include resource details',
    is_flag=True,
    default=False
)
@click.pass_obj
def cmd_list(cfg, verbose):
    cfg.verbose = verbose


@cmd_list.command(name='nodes', help='list nodes')
@click.pass_obj
async def cmd_list_nodes(cfg):
    cmd = command.CmdListNodes(verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cmd_list.command(name='workers', help='list workers')
@click.argument('node')
@click.pass_obj
async def cmd_list_workers(cfg, node):
    cmd = command.CmdListWorkers(node, verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cli.group(name='show', help='show resources')
@click.option(
    '--verbose',
    help='include resource details',
    is_flag=True,
    default=False
)
@click.pass_obj
def cmd_show(cfg, verbose):
    cfg.verbose = verbose


@cmd_show.command(name='fabric', help='show fabric')
@click.pass_obj
async def cmd_show_fabric(cfg):
    cmd = command.CmdShowFabric(verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cmd_show.command(name='node', help='show node')
@click.argument('node')
@click.pass_obj
async def cmd_show_node(cfg, node):
    cmd = command.CmdShowNode(node, verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cmd_show.command(name='worker', help='show worker')
@click.argument('node')
@click.argument('worker')
@click.pass_obj
async def cmd_show_worker(cfg, node, worker):
    cmd = command.CmdShowWorker(node, worker, verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cmd_show.command(name='transport', help='show transport (for router workers)')
@click.argument('node')
@click.argument('worker')
@click.argument('transport')
@click.pass_obj
async def cmd_show_transport(cfg, node, worker, transport):
    cmd = command.CmdShowTransport(node, worker, transport, verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cmd_show.command(name='realm', help='show realm (for router workers)')
@click.argument('node')
@click.argument('worker')
@click.argument('realm')
@click.pass_obj
async def cmd_show_realm(cfg, node, worker, realm):
    cmd = command.CmdShowRealm(node, worker, realm, verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cmd_show.command(name='component', help='show component (for container and router workers)')
@click.argument('node')
@click.argument('worker')
@click.argument('component')
@click.pass_obj
async def cmd_show_component(cfg, node, worker, component):
    cmd = command.CmdShowComponent(node, worker, component, verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cli.command(name='current', help='currently selected resource')
@click.pass_obj
async def cmd_current(cfg):
    _app.print_selected()


@cli.group(name='select', help='change current resource')
@click.pass_obj
def cmd_select(cfg):
    pass


@cmd_select.command(name='node', help='change current node')
@click.argument('resource')
@click.pass_obj
async def cmd_select_node(cfg, resource):
    _app.current_resource_type = u'node'
    _app.current_resource = resource
    _app.print_selected()


@cmd_select.command(name='worker', help='change current worker')
@click.argument('resource')
@click.pass_obj
async def cmd_select_worker(cfg, resource):
    _app.current_resource_type = u'worker'
    _app.current_resource = resource
    _app.print_selected()


@cmd_select.command(name='transport', help='change current transport')
@click.argument('resource')
@click.pass_obj
async def cmd_select_transport(cfg, resource):
    _app.current_resource_type = u'transport'
    _app.current_resource = resource
    _app.print_selected()


def main():
    """
    Main entry point into CLI.
    """
    click.clear()
    cli()


if __name__ == '__main__':
    main()
