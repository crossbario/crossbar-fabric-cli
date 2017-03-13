
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

### Router Workers

#### Web Resources

##### Static Web Resources

To start a new Static Web Resource on a Web transport:

```console
>> start web-resource --url "/static" --type static --directory "../web/static" node1 router1 transport3 resource1
```

**Reference**

* `--type`
* `--directory`
* `--package`
* `--resource`
* `--options-enable_directory_listing`
* `--options-mime_types`
* `--options-cache_timeout`

##### WSGI Web Resources

**Reference**

* `--type`
* `--module`
* `--object`
* `--minthreads`
* `--maxthreads`


### Guest Workers

#### Starting Guest Workers

Guest workers are worker processes with an arbitrary, user-specified executable started and supervised by the Crossbar.io node controller process.

For example, you might have an backend application component written in JavaScript using AutobahnJS. Here is how to start a guest worker `guest1` on `node1` starting the executable `/usr/bin/nodejs` with a single argument `../client.js`:

```console
>> start worker --type guest --executable "/usr/bin/nodejs" --argument "../client.js" node1 guest1
```

> Note: `--argument` can be repeated multiple times to provide multiple command line argument to the executable started. The argument will be provided to the executable in the same order as the `--argument` option.

When using a local node configuration (eg `config.json`), above command would correspond to the following snippet:

```json
{
    "id": "guest1",
    "type": "guest",
    "executable": "/usr/bin/nodejs",
    "arguments": ["../client.js"]
}
```

> Note: As usual, by default, the working directory of a guest worker is the node directory (where the `config.json` resides). So, `../client.js` goes one dir up from `.crossbar` and looks for a `client.js` to run under NodeJS.

Again, everything that can be done via a local node configuration file is supported from Crossbar.io Fabric shell too.

For example, take this more complex example of a guest worker (this is from our live demos instance):

```json
{
    "id": "guest1",
    "type": "guest",
    "executable": "/usr/bin/nodejs",
    "arguments": [
        "backend_complete.js"
    ],
    "options": {
        "workdir": "../backend",
        "watch": {
            "directories": [
                "../backend"
            ],
            "action": "restart"
        }
    }
}
```

Here is the shell command that does the same:

```console
>> start worker \
    --type guest \
    --executable "/usr/bin/nodejs" \
    --argument "backend_complete.js" \
    --options-workdir "../backend" \
    --options-watch-directory "../backend" \
    --options-watch-action restart \
node1 guest1
```

**Reference**

* `--type`: must be `guest` for a guest worker
* `--executable`: absolute path to executable (or only executable, if it can be resolved)
* `--argument`: command line argument to executable
* `--options-workdir`: working directory (absolute path or relative to Crossbar.io node directory)
* `--options-env-inherit`: true or false
* `--options-env-inherit`: environment variable to inherit
* `--options-env-var`: environment variable setting `"X=y"`
* `--options-stdin`: one of `close`
* `--options-stdin-type`: one of `json`, `yaml`
* `--options-stdin-value`: a JSON (or YAML) serialized string
* `--options-stdin-close`: true or false
* `--options-stdout`: one of `close`, `log`, `drop`
* `--options-stderr`: one of `close`, `log`, `drop`
* `--options-watch-directory`: directory to be watched
* `--options-watch-action`: one of `restart`
