

sudo apt install keychain
keychain --agents ssh,gpg



Tom Prince <tom.prince@twistedmatrix.com>

Hi Tom,

thanks for getting back to me. Rgd areas of work, there are many. Let me describe some.

In the bigger picture, we're doing a lot of OSS with Crossbar.io and the Autobahn client libraries. The latter are Python, but other languages as well.

Then we are developing closed bits, which are part of the commercial offering (as we have a commercial OSS business model).

There is work in all of above. The latter currently more urgent than the former.

So for example, with the OSS bits, there are issues like


which in the end might take 100 LOCs, but go pretty much deep into the routing core of Crossbar.io, which means, it requires a deep understanding of the inner parts and how all fits together.

Similar issues touching the routing core:

https://github.com/crossbario/crossbar/issues/965
https://github.com/crossbario/crossbar/issues/656
https://github.com/crossbario/crossbar/issues/606
https://github.com/crossbario/crossbar/issues/583
https://github.com/crossbario/crossbar/issues/532
https://github.com/crossbario/crossbar/issues/479

These aren't the easiest ones, and of course working on one or more of these would likely require a lot of time getting into the code base and understanding how it works.

So probably not very efficient if you'd be unavailable after short time again, but on the other hand this offers the chance that what you see seems cool - and you stay;)

Within OSS work, I think it could also be very valuable for us if you'd go over our code, review, robustify, write unit tests and learn the code base on the go.


Create a management realm and pair a node:

    >> create management-realm oberstet

    >> pair node --pubkey XXX node1

Start a router, real, role, permission and transport:

    >> start worker --type router node1 router1

    >> start realm --name myrealm node1 router1 realm1

    >> start role --name myrole node1 router1 realm1 role1

    >> start permission --uri "com.example." --match prefix --allow-call true node1 router1 realm1 role1

    >> start transport --type websocket --endpoint-type tcp --endpoint-port 9000 node1 router1 transport2

Start a Web transport and add resources:

    >> start transport --type web --endpoint-type tcp --endpoint-port 8080 node1 router1 transport3

    >> start web-resource --url "/static" --type static --path "../web/static" node1 router1 transport3 resource1


    >> publish component --spec mycomp1.json --readme mycomp1.md "com.example.mycomp1"

    >> start worker --type component --uri "com.example.mycomp1" node1 component1


actions:

- start
- stop
- list
- show


<action> <resource-type> [options] <resource-path>




realm
role
permission


component
transport
resource





## Workers

### Starting a guest worker

Guest workers are worker processes with an arbitrary, user-specified executable started and supervised by the Crossbar.io node controller process.

Here is how to start a guest worker `guest1` on `node1` starting the executable `/usr/bin/nodejs` with a single argument `../client.js` (used when starting the executable):

```console
>> start worker --type guest --executable /usr/bin/nodejs --arguments "../client.js" node1 guest1
```







