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


class CmdPair(Cmd):

    def __init__(self):
        Cmd.__init__(self)


class CmdPairNode(CmdPair):
    """
    GLOBAL REALM: Pair a node to a management realm.
    """

    def __init__(self, realm, pubkey, node_id, authextra=None):
        CmdPair.__init__(self)
        self.realm = realm
        self.pubkey = pubkey
        self.node_id = node_id
        self.authextra = authextra

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.mrealm.pair_node', self.pubkey, self.realm, self.node_id, self.authextra)
        return self._post(session, result)


class CmdCreate(Cmd):

    def __init__(self):
        Cmd.__init__(self)


class CmdCreateManagementRealm(CmdCreate):
    """
    GLOBAL REALM: Create a new management realm.
    """

    def __init__(self, realm):
        CmdCreate.__init__(self)
        self.realm = realm

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.mrealm.create_realm', self.realm)
        return self._post(session, result)


class CmdList(Cmd):

    def __init__(self):
        Cmd.__init__(self)


class CmdListManagementRealms(CmdList):
    """
    GLOBAL REALM: Get list of management realms.
    """

    def __init__(self):
        CmdList.__init__(self)

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.mrealm.get_realms')
        return self._post(session, result)


class CmdListNodes(CmdList):
    """
    GLOBAL REALM: Get list of nodes in management realms.
    """

    def __init__(self, verbose=False):
        CmdList.__init__(self, verbose)

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.mrealm.get_nodes', verbose=self.verbose)
        return self._post(session, result)


class CmdListWorkers(CmdList):
    """
    MREALM: Get list of workers on a node.
    """

    def __init__(self, node, verbose=False):
        CmdList.__init__(self, verbose)
        self.node = node

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.list_workers', self.node, verbose=self.verbose)
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
        result = await session.call(u'crossbarfabriccenter.show_fabric', verbose=self.verbose)
        return self._post(session, result)


class CmdShowNode(CmdShow):

    def __init__(self, node, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.show_node', self.node, verbose=self.verbose)
        return self._post(session, result)


class CmdShowWorker(CmdShow):

    def __init__(self, node, worker, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.show_worker', self.node, self.worker, verbose=self.verbose)
        return self._post(session, result)


class CmdShowTransport(CmdShow):

    def __init__(self, node, worker, transport, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker
        self.transport = transport

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.show_transport', self.node, self.worker, self.transport, verbose=self.verbose)
        return self._post(session, result)


class CmdShowRealm(CmdShow):

    def __init__(self, node, worker, realm, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker
        self.realm = realm

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.show_realm', self.node, self.worker, self.realm, verbose=self.verbose)
        return self._post(session, result)


class CmdShowComponent(CmdShow):

    def __init__(self, node, worker, component, verbose=False):
        CmdShow.__init__(self, verbose)
        self.node = node
        self.worker = worker
        self.component = component

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.show_component', self.node, self.worker, self.component, verbose=self.verbose)
        return self._post(session, result)


class CmdStart(Cmd):

    def __init__(self):
        Cmd.__init__(self)


class CmdStartWorker(CmdStart):

    def __init__(self, node_id, worker_id, worker_type, worker_options=None):
        CmdStart.__init__(self)
        self.node_id = node_id
        self.worker_id = worker_id
        self.worker_type = worker_type
        self.worker_options = worker_options

    async def run(self, session):
        self._pre(session)
        result = await session.call(u'crossbarfabriccenter.start_worker',
                                    node_id=self.node_id,
                                    worker_id=self.worker_id,
                                    worker_type=self.worker_type,
                                    worker_options=self.worker_options)
        return self._post(session, result)


class CmdStartContainerWorker(CmdStart):

    def __init__(self, node_id, worker_id, process_title=None):
        CmdStart.__init__(self)
        self.node_id = node_id
        self.worker_id = worker_id
        self.process_title = process_title

    async def run(self, session):
        self._pre(session)

        options = {}
        if self.process_title:
            options[u'title'] = self.process_title

        result = await session.call(u'crossbarfabriccenter.start_worker',
                                    node_id=self.node_id,
                                    worker_id=self.worker_id,
                                    worker_type=u'container',
                                    worker_options=options)
        return self._post(session, result)


class CmdStartContainerComponent(CmdStart):

    def __init__(self, node_id, worker_id, component_id,
                 classname,
                 realm,
                 transport_type,
                 transport_ws_url,
                 transport_endpoint_type,
                 transport_tcp_host,
                 transport_tcp_port):
        CmdStart.__init__(self)
        self.node_id = node_id
        self.worker_id = worker_id
        self.component_id = component_id
        self.classname = classname
        self.realm = realm
        self.transport_type = transport_type
        self.transport_ws_url = transport_ws_url
        self.transport_endpoint_type = transport_endpoint_type
        self.transport_tcp_host = transport_tcp_host
        self.transport_tcp_port = transport_tcp_port

    async def run(self, session):
        self._pre(session)

        config = {
            u'type': u'class',
            u'transport': {
                u'type': self.transport_type,
                u'endpoint': {
                    u'type': self.transport_endpoint_type
                }
            }
        }
        if self.classname:
            config[u'classname'] = self.classname
        if self.realm:
            config[u'realm'] = self.realm

        if self.transport_type == u'websocket':
            config[u'transport'][u'url'] = self.transport_ws_url

        if self.transport_endpoint_type == u'tcp':
            config[u'transport'][u'endpoint'][u'host'] = self.transport_tcp_host
            config[u'transport'][u'endpoint'][u'port'] = self.transport_tcp_port

        result = await session.call(u'crossbarfabriccenter.start_container_component',
                                    node_id=self.node_id,
                                    worker_id=self.worker_id,
                                    component_id=self.component_id,
                                    config=config)
        return self._post(session, result)
