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

import pprint
from autobahn.util import rtime


class CmdRunResult(object):

    def __init__(self, result, duration=None):
        self.result = result
        self.duration = duration

    def __str__(self):
        if self.duration:
            return u'{}\n\nFinished in {} ms.'.format(self.result, self.duration)
        else:
            return u'{}\n\nFinished successfully.'.format(self.result)


class Cmd(object):
    pass


class CmdList(Cmd):

    def __init__(self, verbose=False):
        Cmd.__init__(self)
        self.verbose = verbose


class CmdListNodes(CmdList):

    def __init__(self, verbose=False):
        CmdList.__init__(self, verbose)

    async def run(self, session):
        if session:
            started = rtime()
            result = await session.call(u'com.example.list_nodes', verbose=self.verbose)
            ended = rtime()
            duration = round(1000. * (ended - started), 1)
            return CmdRunResult(result, duration)
        else:
            raise Exception('not connected')


class CmdListWorkers(CmdList):

    def __init__(self, node, verbose=False):
        CmdList.__init__(self, verbose)
        self.node = node

    async def run(self, session):
        if session:
            started = rtime()
            result = await session.call(u'com.example.list_workers', self.node, verbose=self.verbose)
            ended = rtime()
            duration = round(1000. * (ended - started), 1)
            return CmdRunResult(result, duration)
        else:
            raise Exception('not connected')


class CmdShow(Cmd):

    def __init__(self, verbose=False):
        Cmd.__init__(self)
        self.verbose = verbose


class CmdShowFabric(CmdShow):

    def __init__(self, verbose=False):
        CmdShow.__init__(self, verbose)

    async def run(self, session):
        if session:
            started = rtime()
            result = await session.call(u'com.example.show_fabric', verbose=self.verbose)
            ended = rtime()
            duration = round(1000. * (ended - started), 1)
            return CmdRunResult(result, duration)
        else:
            raise Exception('not connected')


class CmdShowNode(CmdShow):

    def __init__(self, node, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node

    async def run(self, session):
        if session:
            started = rtime()
            result = await session.call(u'com.example.show_node', verbose=self.verbose)
            ended = rtime()
            duration = round(1000. * (ended - started), 1)
            return CmdRunResult(result, duration)
        else:
            raise Exception('not connected')


class CmdShowWorker(CmdShow):

    def __init__(self, node, worker, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker

    async def run(self, session):
        if session:
            started = rtime()
            result = await session.call(u'com.example.show_worker', self.node, verbose=self.verbose)
            ended = rtime()
            duration = round(1000. * (ended - started), 1)
            return CmdRunResult(result, duration)
        else:
            raise Exception('not connected')
