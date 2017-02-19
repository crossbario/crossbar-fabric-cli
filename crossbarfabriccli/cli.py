import click
import json

def pprint_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=4))


class Config(object):

    debug = True



@click.group(help="Crossbar.io Fabric Command Line")
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
def main(ctx, debug, json):
    cfg = Config()
    cfg.debug = debug
    cfg.output = 'json' if json else 'text'

    # remember parameters in CLI context
    ctx.obj = cfg


from crossbarfabriccli import __version__

@main.command()
@click.pass_obj
def version(cfg):
    if cfg.output == 'text':
        print("Crossbar.io Fabric CLI version: {}".format(__version__))
    elif cfg.output == 'json':
        pprint_json({u'version': __version__})
    else:
        raise Exception('internal error')
