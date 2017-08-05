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

from prompt_toolkit import prompt_async
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

import txaio
txaio.use_asyncio()

import asyncio
from autobahn.wamp import cryptosign
from autobahn.wamp.types import ComponentConfig
from autobahn.wamp.exception import ApplicationError
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class ShellClient(ApplicationSession):

    def onConnect(self):
        self.log.info("connected to router")

        # authentication extra information for wamp-cryptosign
        #
        key = self.config.extra[u'key'].key
        extra = {
            # forward the client pubkey: this allows us to omit authid as
            # the router can identify us with the pubkey already
            u'pubkey': key.public_key(),

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
        for k in [u'activation_code', u'request_new_activation_code']:
            if k in self.config.extra and self.config.extra[k]:
                extra[k] = self.config.extra[k]

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
        key = self.config.extra[u'key'].key
        signed_challenge = key.sign_challenge(self, challenge)

        # send back the signed challenge for verification
        return signed_challenge

    async def onJoin(self, details):

        self.log.info("session joined: {details}", details=details)
        self.log.info("*** Hooray! We've been successfully authenticated with WAMP-cryptosign using Ed25519! ***")

        self._ticks = 0
        def on_tick(tick):
            self._ticks += 1

        await self.subscribe(on_tick, u'com.crossbario.fabric.tick')

        done = self.config.extra.get(u'done', None)
        if done and not done.done():
            done.set_result(details)

        self.log.info("session ready!")

    def onLeave(self, details):
        self.log.info("session closed: {details}", details=details)

        # reason=<wamp.error.authentication_failed>
        if details.reason != u'wamp.close.normal':
            done = self.config.extra.get(u'done', None)
            if done and not done.done():
                done.set_exception(ApplicationError(details.reason, details.message))

        self.disconnect()

    def onDisconnect(self):
        loop = asyncio.get_event_loop()
        loop.stop()
