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
        return u'CmdRunResult(result={}, duration={})'.format(self.result, self.duration)


class Cmd(object):

    def __init__(self):
        self._started = None

    def _pre(self, session):
        if not session:
            raise Exception('not connected')
        self._started = rtime()

    def _post(self, session, result):
        duration = round(1000. * (rtime() - self._started), 1)
        self._started = None
        return CmdRunResult(result, duration)



class CmdCreate(Cmd):

    def __init__(self):
        Cmd.__init__(self)


class CmdCreateManagementRealm(CmdCreate):

    def __init__(self, realm):
        CmdCreate.__init__(self)
        self.realm = realm

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.create_management_realm', self.realm)
        return self._post(session, result)


class CmdList(Cmd):

    def __init__(self, verbose=False):
        Cmd.__init__(self)
        self.verbose = verbose


class CmdListManagementRealms(CmdList):

    def __init__(self, verbose=False):
        CmdList.__init__(self, verbose)

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.list_management_realms', verbose=self.verbose)
        return self._post(session, result)


class CmdListNodes(CmdList):

    def __init__(self, verbose=False):
        CmdList.__init__(self, verbose)

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.list_nodes', verbose=self.verbose)
        return self._post(session, result)


class CmdListWorkers(CmdList):

    def __init__(self, node, verbose=False):
        CmdList.__init__(self, verbose)
        self.node = node

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.list_workers', self.node, verbose=self.verbose)
        return self._post(session, result)


class CmdShow(Cmd):

    def __init__(self, verbose=False):
        Cmd.__init__(self)
        self.verbose = verbose

class CmdShowFabric(CmdShow):

    def __init__(self, verbose=False):
        CmdShow.__init__(self, verbose)

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.show_fabric', verbose=self.verbose)
        return self._post(session, result)


class CmdShowNode(CmdShow):

    def __init__(self, node, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.show_node', self.node, verbose=self.verbose)
        return self._post(session, result)


class CmdShowWorker(CmdShow):

    def __init__(self, node, worker, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.show_worker', self.node, self.worker, verbose=self.verbose)
        return self._post(session, result)


class CmdShowTransport(CmdShow):

    def __init__(self, node, worker, transport, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker
        self.transport = transport

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.show_transport', self.node, self.worker, self.transport, verbose=self.verbose)
        return self._post(session, result)


class CmdShowRealm(CmdShow):

    def __init__(self, node, worker, realm, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker
        self.realm = realm

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.show_realm', self.node, self.worker, self.realm, verbose=self.verbose)
        return self._post(session, result)


class CmdShowComponent(CmdShow):

    def __init__(self, node, worker, component, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker
        self.component = component

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'com.crossbario.fabric.show_component', self.node, self.worker, self.component, verbose=self.verbose)
        return self._post(session, result)
