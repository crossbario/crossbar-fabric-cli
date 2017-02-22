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

from __future__ import absolute_import

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp import auth

__all__ = ('run_commands')


def run_commands(params, commands):
    """
    Run a series of commands on CDC.

    :param params: Connection and credential parameters.
    :type params: dict
    :param commands: List of commands to execute on CDC.
    :type commands: list of cdc.command.Command objects
    """
    extra = {
        'verbose': params['verbose'],
        'user': params['user'],
        'key': params['key'],
        'output': params['output'],
        'commands': commands
    }
    runner = ApplicationRunner(url=params['router'], realm=params['realm'], extra=extra, debug_wamp=False)
    runner.run(CdcSession)


class CdcSession(ApplicationSession):
    """
    WAMP application session under which the CLI will connect to CDC.
    """

    def onConnect(self):
        self._verbose = self.config.extra['verbose']
        self._output = self.config.extra['output']
        authid = self.config.extra['user']
        realm = self.config.realm
        if self._verbose:
            print("Connected. Joining realm '{}' as '{}' ..".format(realm, authid))
        self.join(realm, [u"wampcra"], authid)

    def onChallenge(self, challenge):
        if challenge.method == u"wampcra":
            authkey = self.config.extra['key'].encode('utf8')
            signature = auth.compute_wcs(authkey, challenge.extra['challenge'].encode('utf8'))
            return signature.decode('ascii')
        else:
            raise Exception("don't know how to compute challenge for authmethod {}".format(challenge.method))

    @inlineCallbacks
    def onJoin(self, details):
        # print_cdc(self.config.extra, details)
        if self._verbose:
            print("Session attached: {}".format(details))

        try:
            for cmd in self.config.extra['commands']:
                yield cmd.run(self, output=self._output)
        except Exception as e:
            print("Error while running commands: {}".format(e))

        self.leave()

    def onLeave(self, details):
        if details.reason != u"wamp.close.normal" or self._verbose:
            print("{}: {}".format(details.reason, details.message))
        self.disconnect()

    def onDisconnect(self):
        if self._verbose:
            print("Disconnected.")
        reactor.stop()
