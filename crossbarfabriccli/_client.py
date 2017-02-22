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

import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp import cryptosign

from autobahn.wamp.exception import ApplicationError


class ClientSession(ApplicationSession):

    def __init__(self, config=None):
        self.log.info("initializing component: {config}", config=config)
        ApplicationSession.__init__(self, config)

        self._key = config.extra[u'key'].key
        self.log.info("client public key loaded: {}".format(self._key.public_key()))

    def onConnect(self):
        self.log.info("connected to router")

        # authentication extra information for wamp-cryptosign
        #
        extra = {
            # forward the client pubkey: this allows us to omit authid as
            # the router can identify us with the pubkey already
            u'pubkey': self._key.public_key(),

            # not yet implemented. a public key the router should provide
            # a trustchain for it's public key. the trustroot can eg be
            # hard-coded in the client, or come from a command line option.
            u'trustroot': None,

            # not yet implemented. for authenticating the router, this
            # challenge will need to be signed by the router and send back
            # in AUTHENTICATE for client to verify. A string with a hex
            # encoded 32 bytes random value.
            u'challenge': None,

            u'channel_binding': u'tls-unique',
        }

        # used for user login/registration activation code
        if u'activation_code' in self.config.extra and self.config.extra[u'activation_code']:
            extra[u'activation_code'] = self.config.extra[u'activation_code']

        # now request to join ..
        self.join(self.config.realm,
                  authmethods=[u'cryptosign'],
                  authid=self.config.extra.get(u'authid', None),
                  authrole=self.config.extra.get(u'authrole', None),
                  authextra=extra)

    def onChallenge(self, challenge):
        self.log.info("authentication challenge received: {challenge}", challenge=challenge)
        # alright, we've got a challenge from the router.

        # not yet implemented. check the trustchain the router provided against
        # our trustroot, and check the signature provided by the
        # router for our previous challenge. if both are ok, everything
        # is fine - the router is authentic wrt our trustroot.

        # sign the challenge with our private key.
        signed_challenge = self._key.sign_challenge(self, challenge)

        # send back the signed challenge for verification
        return signed_challenge

    def onJoin(self, details):
        self.log.info("session joined: {details}", details=details)
        self.log.info("*** Hooray! We've been successfully authenticated with WAMP-cryptosign using Ed25519! ***")

        done = self.config.extra.get(u'done', None)
        if done and not done.called:
            done.callback(details)

        #self.leave()

    def onLeave(self, details):
        self.log.info("session closed: {details}", details=details)

        # reason=<wamp.error.authentication_failed>
        if details.reason != u'wamp.close.normal':
            done = self.config.extra.get(u'done', None)
            if done and not done.called:
                done.errback(ApplicationError(details.reason, details.message))

        self.disconnect()

    def onDisconnect(self):
        self.log.info("connection to router closed")

#        try:
#            reactor.stop()
#        except ReactorNotRunning:
#            pass

