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

from __future__ import absolute_import

import sys
import json
from pprint import pprint

import click

from autobahn.util import utcnow


HIGHLIGHT_FG = 'yellow'
HIGHLIGHT_BG = 'black'

PLEN = 40
MLEN = 112

CDC = """        ________  _____
       / ___/ _ \/ ___/      {now}
      / /__/ // / /__        Realm: {realm}, Router: {router}
      \___/____/\___/        Session: {session}, Auth ID: {authid}, Auth Role: {authrole}

"""

def pprint_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=4))


def logline(prefix, message):
    click.echo(click.style(("{:>" + str(PLEN) + "}").format(prefix), bg=HIGHLIGHT_BG, fg=HIGHLIGHT_FG), nl=False)
    message = " {}".format(message)
    if len(message) > MLEN - 3:
        message = message[:MLEN - 3] + ".."
    click.echo(message)


def logerr(error, message):
    click.echo(click.style(("{:>" + str(PLEN) + "}").format(error), bg='red', fg=HIGHLIGHT_FG), nl=False)
    message = " {}".format(message)
    if len(message) > MLEN - 3:
        message = message[:MLEN - 3] + ".."
    click.echo(message)


def getv(path, data):
    res = data
    for p in path.split('.'):
        if p in res:
            res = res[p]
        else:
            break
    return res


def print_cdc(extra, details, short=True, silent=False):
    if silent:
        return
    if short:
        msg = "Crossbar.io DevOps Center ({} on {})".format(details.authid, details.realm)
        msg = "{:^120}\n".format(msg)
    else:
        kwargs = {
            'now': utcnow(),
            'router': extra['params']['router'],
            'realm': details.realm,
            'session': details.session,
            'authid': details.authid,
            'authrole': details.authrole
        }
        msg = CDC.format(**kwargs)
        msg = ''.join("{:120}\n".format(line) for line in msg.splitlines())
    click.echo(click.style(msg, bg='black', fg='yellow', bold=True))


def print_table(title, headers, data):
    col_cnt = len(headers)
    col_widths = {}
    col_ids = {}

    for i in range(col_cnt):
        col_ids[i] = headers[i]['field']
        if i not in col_widths:
            col_widths[i] = 0
        s = "{}".format(headers[i]['title'])
        if len(s) > col_widths[i]:
            col_widths[i] = len(s)

    for row in data:
        for i in range(col_cnt):
            val = getv(col_ids[i], row)
            s = "{}".format(val)
            if len(s) > col_widths[i]:
                col_widths[i] = len(s)

    total_width = 0
    for i in range(col_cnt):
        col_widths[i] += 3
        total_width += col_widths[i]

    msg = ("{:^" + str(total_width) + "}").format(title)
    click.echo(click.style(msg, bg=HIGHLIGHT_BG, fg=HIGHLIGHT_FG, bold=True), nl=True)

    for i in range(col_cnt):
        msg = ("{:>" + str(col_widths[i]) + "}").format(headers[i]['title'])
        click.echo(click.style(msg, bg=HIGHLIGHT_BG, fg=HIGHLIGHT_FG, bold=False), nl=False)
    click.echo()

    for row in data:
        for i in range(col_cnt):
            val = getv(col_ids[i], row)
            click.echo(("{:>" + str(col_widths[i]) + "}").format(val), nl=False)
        click.echo()

    click.echo()


def print_vmprof(profile, indent=1, prune_percent=5., prune_level=1000):
    for rec in profile:
        try:
            if float(rec.get('perc', 0)) >= prune_percent:
                if rec['type'] == 'py':
                    p2 = click.style(rec['fun'], fg='blue', bold=True)
                    p2b = click.style(('.' * rec['level'] * indent), fg='blue', bold=False)
                    p3 = []
                    if rec['dirname']:
                        p3.append(click.style(rec['dirname'] + '/', fg='white', bold=False))
                    p3.append(click.style(rec['basename'], fg='white', bold=True) + ':')
                    p3.append(click.style("{}".format(rec['line']), fg='white', bold=False))
                    p3 = ''.join(p3)

                elif rec['type'] == 'jit':
                    p2 = click.style("JIT code", fg='red', bold=True)
                    p2b = click.style(('.' * rec['level'] * indent), fg='red', bold=False)
                    p3 = click.style(rec['fun'], fg='white', bold=False)

                else:
                    raise Exception("fail!")

                p1 = click.style("{:>5}%".format(rec['perc']), fg='white', bold=True)
                p4 = click.style("{}%".format(rec['perc_of_parent']), fg='white', bold=True)

                print("{} {} {}  {}  {}".format(p1, p2b, p2, p4, p3))
        except Exception as e:
            print(e)
