#####################################################################################
#
#  Copyright (c) Crossbar.io Technologies GmbH
#
#  Unless a separate license agreement exists between you and Crossbar.io GmbH (e.g.
#  you have purchased a commercial license), the license terms below apply.
#
#  Should you enter into a separate license agreement after having received a copy of
#  this software, then the terms of such license agreement replace the terms below at
#  the time at which such license agreement becomes effective.
#
#  In case a separate license agreement ends, and such agreement ends without being
#  replaced by another separate license agreement, the license terms below apply
#  from the time at which said agreement ends.
#
#  LICENSE TERMS
#
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License, version 3, as published by the
#  Free Software Foundation. This program is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#
#####################################################################################

import argparse
import json
import pprint
import os

from jinja2 import Environment, FileSystemLoader

import txaio
txaio.use_asyncio()

from cbsh.util import hl


# e & e approach: flatc, sphinx, vscode, ..

#
# Jinja2 based code generator, 2 steps:
#
# 1. set of target files = [(target_filename, source_template)], computed by (single) meta template file
# 2. render set of target files, computed by individual template files
#

def process(schema):
    # http://jinja.pocoo.org/docs/latest/api/#loaders
    loader = FileSystemLoader(['/path/to/templates', '/other/path'], encoding='utf-8', followlinks=False)

    env = Environment(loader=loader)

    tmpl = env.get_template('example')

    print(tmpl)

    contents = tmpl.render(the='variables', go='here')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'infile', help='FlatBuffers JSON schema input file (.json)')
    parser.add_argument(
        '-t', '--templates', help='Templates folder')
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Enable verbose processing output.')
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Enable debug output.')

    options = parser.parse_args()

    log = txaio.make_logger()
    txaio.start_logging(level='debug' if options.debug else 'info')

    infile_path = os.path.abspath(options.infile)
    with open(infile_path, 'rb') as f:
        buf = f.read()

    log.info('Loading FlatBuffers JSON schema ({} bytes) ...'.format(
        len(buf)))

    try:
        schema = json.loads(buf, encoding='utf8')
    except Exception as e:
        log.error(e)

    if options.verbose:
        log.info('Schema metadata:')
        schema_meta_str = pprint.pformat(schema['meta'])
        # log.info(schema_meta_str)
        # log.info('{}'.format(schema_meta_str))
        print(schema_meta_str)

        for o in schema['types'].values():
            if o['type'] == 'interface':
                log.info('interface: {}'.format(hl(o['name'], bold=True)))
                for s in o['slots'].values():
                    log.info('{:>12}: {}'.format(s['type'], hl(s['name'])))
