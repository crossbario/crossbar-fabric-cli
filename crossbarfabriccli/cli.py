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

_old_click_argument = click.argument

import inspect
from click import Argument
from click.decorators import _param_memo

def _new_click_argument(*param_decls, **attrs):
    """Attaches an argument to the command.  All positional arguments are
    passed as parameter declarations to :class:`Argument`; all keyword
    arguments are forwarded unchanged (except ``cls``).
    This is equivalent to creating an :class:`Argument` instance manually
    and attaching it to the :attr:`Command.params` list.
    :param cls: the argument class to instantiate.  This defaults to
                :class:`Argument`.
    """
    def decorator(f):
        if 'help' in attrs:
            attrs['help'] = inspect.cleandoc(attrs['help'])
        ArgumentClass = attrs.pop('cls', Argument)
        _param_memo(f, ArgumentClass(param_decls, **attrs))
        return f
    return decorator

click.argument = _new_click_argument


from crossbarfabriccli import app, command


USAGE = """
Examples:
To start the interactive shell, use the "shell" command:

    cbf shell

You can run the shell under different user profile
using the "--profile" option:

    cbf --profile mister-test1 shell
"""


# the global, singleton app object
_app = app.Application()


class Config(object):
    """
    Command configuration object where we collect all the parameters,
    options etc for later processing.
    """

    def __init__(self, app, profile):
        self.app = app
        self.profile = profile
        self.verbose = None
        self.resource_type = None
        self.resource = None

    def __str__(self):
        return u'Config(verbose={}, resource_type={}, resource={})'.format(self.verbose, self.resource_type, self.resource)


@click.group(invoke_without_command=True)
@click.option(
    '--profile',
    help='profile to use',
    default=u'default'
)
@click.pass_context
def cli(ctx, profile):
    ctx.obj = Config(_app, profile)

    # Allowing a command group to specifiy a default subcommand can be done using
    # https://github.com/click-contrib/click-default-group
    #
    # However, this breaks the click-repl integration for prompt-toolkit:
    #
    # https://github.com/pallets/click/issues/430#issuecomment-282015177
    #
    # Hence, we are using a different (probably less clean) trick - this works.
    #
    if ctx.invoked_subcommand is None:
        ctx.invoke(cmd_shell)


@cli.command(name='login', help='authenticate user profile / key-pair with Crossbar.io Fabric')
@click.option(
    '--code', default=None,
    help="Supply login/registration code",
)
@click.pass_context
def cmd_login(ctx):
    click.echo('authenticating profile "{}" ..'.format(ctx.obj.profile))


@cli.command(name='shell', help='run an interactive Crossbar.io Fabric shell')
@click.pass_context
def cmd_shell(ctx):
    ctx.obj.app.run_context(ctx)


@cli.command(name='clear', help='clear screen')
async def cmd_clear():
    click.clear()


@cli.command(name='help', help='general help')
@click.pass_context
def cmd_help(ctx):
    click.echo(ctx.parent.get_help())
    click.echo(USAGE)


@cli.group(name='set', help='change shell settings')
@click.pass_obj
def cmd_set(cfg):
    pass


@cmd_set.group(name='output-verbosity', help='command output verbosity')
@click.pass_obj
def cmd_set_output_verbosity(cfg):
    pass


@cmd_set_output_verbosity.command(name='silent', help='swallow everything including result, but error messages')
@click.pass_obj
def cmd_set_output_verbosity_silent(cfg):
    cfg.app.set_output_verbosity('silent')


@cmd_set_output_verbosity.command(name='result-only', help='only output the plain command result')
@click.pass_obj
def cmd_set_output_verbosity_result_only(cfg):
    cfg.app.set_output_verbosity('result-only')


@cmd_set_output_verbosity.command(name='normal', help='output result and short run-time message')
@click.pass_obj
def cmd_set_output_verbosity_normal(cfg):
    cfg.app.set_output_verbosity('normal')


@cmd_set_output_verbosity.command(name='extended', help='output result and extended execution information.')
@click.pass_obj
def cmd_set_output_verbosity_extended(cfg):
    cfg.app.set_output_verbosity('extended')


@cmd_set.group(name='output-format', help='command output format')
@click.pass_obj
def cmd_set_output_format(cfg):
    pass


@cmd_set_output_format.command(name='json', help='set JSON output format')
@click.pass_obj
def cmd_set_output_format_json(cfg):
    cfg.app.set_output_format('json')


@cmd_set_output_format.command(name='json-color', help='set JSON+color output format')
@click.pass_obj
def cmd_set_output_format_json_color(cfg):
    cfg.app.set_output_format('json-color')


@cmd_set_output_format.command(name='yaml', help='set YAML format')
@click.pass_obj
def cmd_set_output_format_yaml(cfg):
    cfg.app.set_output_format('yaml')


@cmd_set_output_format.command(name='yaml-color', help='set YAML+color output format')
@click.pass_obj
def cmd_set_output_format_yaml_color(cfg):
    cfg.app.set_output_format('yaml-color')


@cmd_set_output_format.command(name='plain', help='set plain output format')
@click.pass_obj
def cmd_set_output_format_plain(cfg):
    cfg.app.set_output_format('plain')


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
    await cfg.app.run_command(cmd)


@cmd_list.command(name='workers', help='list workers')
@click.argument('node')
@click.pass_obj
async def cmd_list_workers(cfg, node):
    cmd = command.CmdListWorkers(node, verbose=cfg.verbose)
    await cfg.app.run_command(cmd)


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
    await cfg.app.run_command(cmd)


@cmd_show.command(name='node', help='show node')
@click.argument('node')
@click.pass_obj
async def cmd_show_node(cfg, node):
    cmd = command.CmdShowNode(node, verbose=cfg.verbose)
    await cfg.app.run_command(cmd)


@cmd_show.command(name='worker', help='show worker')
@click.argument('node')
@click.argument('worker')
@click.pass_obj
async def cmd_show_worker(cfg, node, worker):
    cmd = command.CmdShowWorker(node, worker, verbose=cfg.verbose)
    await cfg.app.run_command(cmd)


@cmd_show.command(name='transport', help='show transport (for router workers)')
@click.argument('node')
@click.argument('worker')
@click.argument('transport')
@click.pass_obj
async def cmd_show_transport(cfg, node, worker, transport):
    cmd = command.CmdShowTransport(node, worker, transport, verbose=cfg.verbose)
    await cfg.app.run_command(cmd)


@cmd_show.command(name='realm', help='show realm (for router workers)')
@click.argument('node')
@click.argument('worker')
@click.argument('realm')
@click.pass_obj
async def cmd_show_realm(cfg, node, worker, realm):
    cmd = command.CmdShowRealm(node, worker, realm, verbose=cfg.verbose)
    await cfg.app.run_command(cmd)


@cmd_show.command(name='component', help='show component (for container and router workers)')
@click.argument('node')
@click.argument('worker')
@click.argument('component')
@click.pass_obj
async def cmd_show_component(cfg, node, worker, component):
    cmd = command.CmdShowComponent(node, worker, component, verbose=cfg.verbose)
    await cfg.app.run_command(cmd)


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
    cli()


if __name__ == '__main__':
    main()
