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


import click

# https://github.com/click-contrib/click-repl
#from click_repl import register_repl
#import click_repl
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import prompt, prompt_async


from crossbarfabriccli import repl, command

import asyncio
from crossbarfabriccli import client


class Application(object):

    def __init__(self):
        self.current_resource_type = None
        self.current_resource = None
        self.session = None

    def print_cwd(self):
        click.echo('{} -> {}.\n'.format(self.current_resource_type, self.current_resource))

    def cwd(self):
        return self.current_resource_type, self.current_resource

    def __str__(self):
        return u'App(current_resource_type={}, current_resource={})'.format(self.current_resource_type, self.current_resource)

_app = Application()


class Config(object):

    def __init__(self, app):
        self.app = app
        self.verbose = None
        self.resource_type = None
        self.resource = None

    def __str__(self):
        return u'Config(verbose={}, resource_type={}, resource={})'.format(self.verbose, self.resource_type, self.resource)



async def run_command(cmd, session):
    result = await cmd.run(session)
    click.echo(result)


WELCOME = """
Welcome to Crossbar.io Fabric Shell!

Press Ctrl-C to cancel the current command, and Ctrl-D to exit the shell.
Type "help" to get help. Try TAB for auto-completion.

"""

def run_context(ctx):
    click.echo(WELCOME)
    loop = asyncio.get_event_loop()

    ctx.obj.app.session = client.run()

    prompt_kwargs = {
        'history': FileHistory('cbf-history'),
    }
    shell_task = loop.create_task(repl.repl(ctx, prompt_kwargs=prompt_kwargs))

    loop.run_until_complete(shell_task)
    loop.close()


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = Config(_app)


@cli.command(help='Run an interactive shell')
@click.pass_context
def run(ctx):
    run_context(ctx)


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
@click.pass_obj
async def cmd_show_node(cfg):
    cmd = command.CmdShowNode(verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)


@cmd_show.command(name='worker', help='show worker')
@click.argument('node')
@click.pass_obj
async def cmd_show_worker(cfg, node):
    cmd = command.CmdShowWorker(node, verbose=cfg.verbose)
    await run_command(cmd, cfg.app.session)




#:@cmd_stop.command(name='transport', help='Stop a router transport.')
#@click.argument('resource')
#@click.option(
#    '--mode',
#    help=u'graceful: wait for all clients to disconnect before stopping\n\nimmediate: stop transport forcefully disconnecting all clients',
#    type=click.Choice([u'graceful', u'immediate']),
#    default=u'graceful'
#)
#@click.pass_obj
#def cmd_stop_transport(cfg, resource, mode):
#    cfg.resource_type = u'transport'
#    cfg.resource = resource
#    click.echo(cfg)
#    click.echo(_app)



@cli.command(name='pwd', help='print current resource')
@click.pass_obj
async def cmd_pwd(cfg):
    _app.print_cwd()


@cli.group(name='cd', help='change current resource')
@click.pass_obj
def cmd_cd(cfg):
    pass


@cmd_cd.command(name='node', help='change current node')
@click.argument('resource')
@click.pass_obj
async def cmd_cd_node(cfg, resource):
    """
    Change current resource
    """
    _app.current_resource_type = u'node'
    _app.current_resource = resource
    _app.print_cwd()


@cmd_cd.command(name='worker', help='change current worker')
@click.argument('resource')
@click.pass_obj
async def cmd_cd_worker(cfg, resource):
    _app.current_resource_type = u'worker'
    _app.current_resource = resource
    _app.print_cwd()


@cmd_cd.command(name='transport', help='change current transport')
@click.argument('resource')
@click.pass_obj
async def cmd_cd_transport(cfg, resource):
    _app.current_resource_type = u'transport'
    _app.current_resource = resource
    _app.print_cwd()


def main():
    """
    Main entry point into CLI.
    """
    click.clear()
    cli()


if __name__ == '__main__':
    main()
