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




@click.group()
@click.option(
    '--verbose',
    is_flag=True,
    default=False
)
@click.pass_context
def _cli(ctx, verbose):
    #print("333", ctx)
    cfg = Config(global_cfg)
    cfg.verbose = verbose
    ctx.obj = cfg


@_cli.command(help='Start in interactive shell mode')
@click.pass_obj
def _shell(cfg):

    import asyncio
    loop = asyncio.get_event_loop()

    prompt_kwargs = {
        'history': FileHistory('cbf-history'),
    }
    shell_task = loop.create_task(repl.repl(click.get_current_context(), prompt_kwargs=prompt_kwargs))

    #click.echo('sdfsdfsd')

    from crossbarfabriccli import client

    #session_task = loop.create_task(client.run())
    #loop.run_until_complete(session_task)

    #global_cfg.session = client.run()
    cfg.app.session = client.run()
    #click.echo(global_cfg.session)

    #return

    loop.run_until_complete(shell_task)
    loop.close()



from autobahn.util import rtime


@cli.command(name='add2', help='Add two numbers by calling remote procedure "com.example.add2"')
@click.argument('x', type=int)
@click.argument('y', type=int)
@click.option(
    '--bias',
    default=0,
    help='Add another constant',
)
@click.pass_obj
async def cmd_add2(cfg, x, y, bias):
    if cfg.app.session:
        started = rtime()
        res = await cfg.app.session.call(u'com.example.add2', x, y + bias)
        ended = rtime()
        duration = round(1000000. * (ended - started))
        click.echo('RPC took {}us'.format(duration))
        click.echo(res)
    else:
        click.echo('sorry, no session')




@cli.command(name='say')
@click.option(
    '--message',
    default=u'Hello, world!',
    help='Set the message to say hello',
)
@click.pass_obj
def cmd_say(cfg, message):
    click.echo(message)




@cli.group(name='cd', help='change current resource')
@click.pass_obj
async def cmd_cd(cfg):
    pass


@cmd_cd.command(name='node', help='change current resource')
@click.argument('resource')
@click.pass_obj
async def cmd_cd_node(cfg, resource):
    """
    Change current resource
    """
    global_cfg.current_resource_type = u'node'
    global_cfg.current_resource = resource
    click.echo(cfg)
    click.echo(global_cfg)

@cmd_cd.command(name='worker')
@click.argument('resource')
@click.pass_obj
def cmd_cd_worker(cfg, resource):
    global_cfg.current_resource_type = u'worker'
    global_cfg.current_resource = resource
    click.echo(cfg)
    click.echo(global_cfg)

@cmd_cd.command(name='transport')
@click.argument('resource')
@click.pass_obj
def cmd_cd_transport(cfg, resource):
    global_cfg.current_resource_type = u'transport'
    global_cfg.current_resource = resource
    click.echo(cfg)
    click.echo(global_cfg)


@cli.group(name='stop', help='Stop a resource.')
@click.pass_obj
def cmd_stop(cfg):
    pass


@cmd_stop.command(name='transport', help='Stop a router transport.')
@click.argument('resource')
@click.option(
    '--mode',
    help=u'graceful: wait for all clients to disconnect before stopping\n\nimmediate: stop transport forcefully disconnecting all clients',
    type=click.Choice([u'graceful', u'immediate']),
    default=u'graceful'
)
@click.pass_obj
def cmd_stop_transport(cfg, resource, mode):
    cfg.resource_type = u'transport'
    cfg.resource = resource
    click.echo(cfg)
    click.echo(global_cfg)


#@cmd_stop.command(name='worker')
#@click.argument('node')
#@click.argument('worker')
#@click.pass_obj
#def cmd_stop_worker(cfg, node, worker):
#    pass
#
#
#@cmd_stop.command(name='realm')
#@click.argument('node')
#@click.argument('worker')
#@click.argument('realm')
#@click.pass_obj
#def cmd_stop_realm(cfg, node, worker, realm):
#    pass






@cli.group(name='start')
@click.pass_obj
def cmd_start(cfg):
    pass


@cmd_start.command(name='worker')
@click.argument('resource')
@click.option(
    '--type',
    required=True
)
@click.pass_obj
def cmd_start_worker(cfg, resource, type):
    pass


@cmd_start.command(name='realm')
@click.argument('resource')
@click.option(
    '--name',
    required=True
)
@click.pass_obj
def cmd_start_realm(cfg, resource, name):
    pass


def main2():
    """
    Main entry point into CLI.
    """
    print(cli)
    print(dir(cli))
    print(cli.invoke)
    #cli.invoke()
    print(cli.__call__)
    #print(help(cli.invoke))

    ctx = click.get_current_context()
    print(ctx)
    return
    #register_repl(cli)
    import asyncio
    loop = asyncio.get_event_loop()

    from crossbarfabriccli import client

    global_cfg.session = client.run()
    print(global_cfg.session)

    #return

    cli_task = loop.create_task(cli())
    loop.run_until_complete(cli_task)


    #try:
    #    loop.run_forever()
    #except KeyboardInterrupt:
    #    # wait until we send Goodbye if user hit ctrl-c
    #    # (done outside this except so SIGTERM gets the same handling)
    #    pass

    loop.close()


def main():
    """
    Main entry point into CLI.
    """
    click.clear()

    ctx = {}

    cli()

    #cli(ctx)
    return

    import asyncio
    loop = asyncio.get_event_loop()

    from crossbarfabriccli import client

    global_cfg.session = client.run()
    print(global_cfg.session)

    #cli_task = loop.create_task(cli())
    #loop.run_until_complete(cli_task)
    #await cli()
    cli_coro = cli()
    cli_task = asyncio.ensure_future(cli_coro)

    #loop.run_until_complete(cli_task)


    try:
        loop.run_forever()
    except KeyboardInterrupt:
        # wait until we send Goodbye if user hit ctrl-c
        # (done outside this except so SIGTERM gets the same handling)
        pass

    loop.close()


if __name__ == '__main__':
    main()
