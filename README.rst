# Fabric CLI

## cbf init

Invoking

```
cbf init
```

initializes cbf:

- if directory `$HOME/.cbf` does not exist, create it
- if `$HOME/.cbf/config` does not exist, create a default one
- if `$HOME/.cbf/userkey.priv|pub` exist, if not, generate them, asking for email in the course

Then try login using email as `authid` and pubkey from `$HOME/.cbf/userkey.pub` as `authextra`.

The userkey pair to use can be overidden using command line options.

If no realm is specified on the command line, cbf will connect to the global realm.

A user can specify a management realm to connect to, which will be necessary for all non top level actions like eg


cbf --realm global info

cbf --realm oberstet list nodes

export CBF_REALM=oberstet

cbf list nodes
cbf list workers --node node7
cbf list components --node node7 --container container6
cbf list realms --node node7 --router router4

cbf register node --node7 <PATH TO NODE PUBLIC KEYFILE>

cbf check node --node node7
cbf check worker --node node7 --worker router4

cbf start worker --node node7 myworker.json
cbf start component --node node2 --worker container6 mycomponent.json
cbf start realm --node node3 --worker router4 myrealm.json
cbf start role --node node4 --worker router4 myrole.json
cbf start permission --node node3 --worker router4 --realm realm1 mypermission.json


cbf start component "node=node2 container=container6 component=component4" mycomponent.json

cbf start component --path "/node/node2/worker/container6/component/component4" mycomponent.json



# CDC CLI

* Overview
   * Introduction
   * Installation
   * Setup
   * General usage
* Configuration & Management
   * Nodes
      * creation
      * modification
      * deletion
   * Workers
      * General
      * Router Workers
         * Permissions
      * Container Workers
      * Transports
      * Guest Workers
* Monitoring
   * Getting statistics
   * Live monitoring


## Overview

### Introduction

`cdc` is a command line interface (CLI) for Crossbar.io DevOps Center (CDC).

`cdc` can be used to manage and monitor a fleet of Crossbar.io nodes remotely. `cdc` connects to CDC issuing commmands, like listing all currently running Crossbar.io nodes or start a new worker on a Crossbar.io node.

'cdc' does not connect directly to Crossbar.io nodes, but works through a connection to a CDC instance:

```
cdc <COMMAND> -----> Crossbar.io DevOps Center (CDC)
                         |
                         v
                         |
                         +---> <COMMAND> --> Crossbar.io node 1
                         +---> <COMMAND> --> Crossbar.io node 2
                         +---> <COMMAND> --> Crossbar.io node 2
```


### Installation

`cdc` is written in Python, using [AutobahnPython](http://autobahn.ws/python). It runs on Python 2 and Python 3, is published on the [Python Package Index](https://pypi.python.org/pypi) and is licensed under the MIT license.

To install:

```console
pip install cdc
```

### Setup

#### Credentials

For `cdc` to connect to the CDC Service, it needs connection and credentials information. By default, `cdc` will look for a file

* `$HOME/.cdc/credentials` (Linux/Mac)
* `%USERPROFILE%\.cdc\credentials` (Windows)

Here is a typical credentials file with a single section for the `default` user profile:

```
[default]
cdc_router = "wss://cdc.crossbar.io"
cdc_realm = "freetier-s04"
cdc_user = "oberstet"
cdc_key = "rP6G5RbKV1k1U7ZZSiXMBUOnZ4MPkeqXJ5czSLyefWM="
```

> Secret keys can be generated using `openssl rand -base64 32`

A credential file can also contain multiple profiles:

```
[default]
cdc_router = ws://cdc.crossbar.io:9000
cdc_realm = cdc-oberstet-1
cdc_user = oberstet
cdc_key = rP6G5RbKV1k1U7ZZSiXMBUOnZ4MPkeqXJ5czSLyefWM=

[local]
cdc_router = ws://127.0.0.1:9000
cdc_realm = cdc-oberstet-1
cdc_user = oberstet
cdc_key = rP6G5RbKV1k1U7ZZSiXMBUOnZ4MPkeqXJ5czSLyefWM=
```

The profile to use can be selected via a command line option:

```console
cdc --profile=local get time
```

or by setting the environment variable `CDC_PROFILE`.

**For security reasons, you should restrict access to the credentials file using file permissions so that only the owner is allowed to read (and write) the file.** In Linux, use chmod 600 to set owner-only permissions. In Windows, use the [Properties window](http://technet.microsoft.com/en-us/library/cc772196.aspx) or use the [icacls](http://technet.microsoft.com/en-us/library/cc753525%28WS.10%29.aspx) command.

> cdc follows [this](http://blogs.aws.amazon.com/security/post/Tx3D6U6WSFGOK2H/A-New-and-Standardized-Way-to-Manage-Credentials-in-the-AWS-SDKs) approach to managing credentials.


### General Usage

### Help

To get global help

```console
cdc --help
```

To get help on a command do e.g.

```console
cdc list --help
```

To get help on a subcommand do e.g.

```console
cdc list nodes --help
```

### Tool Version

To get the version of `cdc`

```console
cdc version
```

### Testing

To test that everything is working, including connection to CDC service and your credentials, here is how to retrieve the current time (UTC) on the CDC service

```console
cdc get time
```

### Choosing your profile

To select the user profile to use for a particular command

```console
cdc --profile=bob get time
```

### Input Values

Many options that need to be provided are simple string or numeric values. However, some operations require JSON data structures as input parameters.

These data structures can be given as a JSON-formatted commandline string, e.g.

```console
cdc create transport \
     --config='{"type": "websocket", "endpoint": {"type": "tcp", "port": 7002}}' \
     "mynode.router1.transport2"
```
via standard input, e.g.

```console
echo '{"type": "websocket", "endpoint": {"type": "tcp", "port": 7002}}' | \
     cdc create transport "mynode.router1.transport2" -
```

or from a file.


## Configuration & Management

'cdc' enables the creation as well as the configuration of nodes, e.g. starting routers, modifying workers and setting permissions.

Configurations are stored in the CDC database. Entries are created, modified and deleted via the respective commands (`create`, `modify`, `delete`).

`create` accepts a full set of configuration data, while `modify` takes a change set. Data in the change set for existing entries results in a change of those entries, while new data results in the entry being added. It is possible to delete an entry by setting its value to `null` in a change set.

The configuration does not contain any configuration data for sub-entities, e.g. the configuration passed when creating a router worker does not contain information about realms. (The `cdc` is mainly intended to affect small changes on a running node.)

An entity in the CDC database can be run (by doing `start`), and the current configuration will apply (entities can only be run if their containing entity is running, e.g. a realm can only be started if the router worker it is on is already running). A cyle of `stop` and `start` restarts with the current settings (there's also `restart` which does this with a single command).

Starting an entity as a default also starts all its sub-entities recursively, e.g. when starting a worker, realms and transports configured within this worker are also started, as are the roles within the realms. To start an entity without the contained sub-entities, e.g. when debugging to see what sub-entity causes problems, set the option `recursive='false'`.

`delete`, when applied to a running entity, defaults to stopping the entity and then deleting it from the database. This default can be overriden with --dontstop, in which case trying to delete a running instance returns an exception.

There are instances where modifications can be applied without a restart of the entity. The `apply` command checks whether this is possible. As a default, if the change set as a whole does not require a restart, it is applied, else an exception is returned. If the `--restart` option is set, then a restart is done if necessary.

All configuration commands give immediate feedback about the outcome of the operation. In addition, the 'cdc' allows the monitoring of activities, which is described further on here.


### Nodes

Nodes as the term is used here are all Crossbar.io instances which exist on a management realm. The existence of a node does not require it to be currently running - its configuration can  simply be stored in the CDC database.

In the following, we'll go throught the lifecycle of a node.

#### Creating

A node is created by doing:

```console
cdc create node <node_id> <node_config>
```

<node_id> is a string which is later used to identify and address the node. This needs to be unique within the management realm.

If no <node_id> is given, then the CDC automatically assigns a unique name (e.g. "mynode23").

<node_config> is a JSON data structure which contains the necessary data to connect to the CDC.

If no configuration data is given, then the CDC automatically creates a default working set of data for the current user and realm.

A sample configuration is:

```javascript
{
   "key": "rffeuCOKDeeKDzIDFo+v2PG8/n9rtSSa8PLQOMiL1ZM=",
   "realm": "cdc-oberstet-1",
   "transport": {
       "type": "websocket",
       "url": "ws://localhost:9000",
       "endpoint": {
           "type": "tcp",
           "host": "127.0.0.1",
           "port": 9000
       }
   }
}
```

#### Starting

Nodes cannot be started by the CDC - since without a node there's no entity to receive a `start`command.

When you start a node (manually, via script etc.), it can only connect to the CDC if its connection data establishes a transport to the CDC and it has the required authentication key.

#### Stopping

To stop a running node do

```console
cdc stop node <node_id>
```

<node_id> is the id of the node unique in the realm.

Stopping a node does not delete it - the node configuration in the database persists. Be aware though that this configuration may have been modified while the node was running, and that in these cases starting the node again will not restore the node as it was at the time it was stopped.

#### Modifying

To modify a node do

```console
cdc modify node <node_id> <change_set>
```

where <node_id> is the id of the node unique in the realm.

The <change_set> is a JSON data structure, which can contain any subset of the configuration data for the node connection, e.g.

```javascript
{
   "transport": {
       "endpoint": {
           "port": 8080
       }
   }
}
```

which would change the transport port from `9000` (as seen in the example configuration for `create`) to `8080`.


#### Deleting

To delete a node, do

```console
cdc delete node <node_id>
```

Deleting a node erases the node configuration from the CDC database, and drops the connection to the node.

The `--stopnode` option stops the node before dropping the connection. Otherwise you're free to manage this on your own (if you want).


#### Attaching an existing node

You can create and then configure a node from the command line (or via the WebUI), but there may be cases where you've started with a local configuration and now want to connect this existing node to the CDC.

This can, on the mere connection level, be done simply by shutting down the node, creating a node on the CDC, adding the connection data to the node configuration and starting it again.

This does not, however, copy the node configuration into the CDC database, so that there's no easy way to modify your existing configuration from then on, since modifications always involve the CDC database.

If you're in a terminal on the machine running the Crossbar.io node, in the directory containing the Crossbar.io configuration, you can do

```console
cdc attach node <node_id>
```

This creates a node in the CDC database, copies the connection data into the local configuration, and copies the local configuration into the database.

<node_id> is optional - if omitted, the CDC just assigns an ID.

`--restart` - if you set this option, the 'cdc' additionally stops the Crossbar.io node and restarts it (this is possible here since the command is executed in the node directory).


### Workers

There are three types of workers: routers, containers and guest workers. They all run within an Crossbar.io node, and a node can run multiple workers, in any mix of types.

We'll first go over the purpose of these and some of the basic differences and then take a look at the lifecycle of each of the three types in turn.

Crossbar.io's main purpose is as a WAMP router. The Crossbar.io process at startup, however, is basically just a shell which is used to run workers (though the mechanics of this shell use WAMP under the hood, and indeed include an internal WAMP router). The WAMP application routing is done by a worker - the router worker (and you can have more than one of these in a Crossbar.io node).

In addition to the WAMP application routing, Crossbar.io can be used to host application components. This means that you can use Crossbar.io to e.g. spin up the entire backend of a WAMP application as part of the startup of the router, using a single configuration.

For hosting application components there are three options:

 - side-by-side components as part of a router worker;
 - container workers;
 - and guest workers.

Usually these components will be part of a WAMP application and connect to a WAMP router (which may run within the same Crossbar.io node, but doesn't need to), but . You can also run a Crossbar.io node without a router worker, just containing container workers and/or guest workers.

##### Side-by-Side and Container Workers

The side-by-side and container worker options both require the application component to be written using the same technical basis as Crossbar.io: Python and the Twisted framework. (Since currently Twisted is not yet fully supported on Python 3, this means Python 2.7.x or PyPy. Support for Python 3 is underway though).

Side-by-side components run *within* a router worker process (so see there for details), while container workers run in a process of their own. In both cases the common technological basis allows tighter integration and more control than with guest workers.

##### Guest Workers

Guest workers can host application components using any runtime available on the system (including Python). A pure Python 3 application, for example, or a C++ component using AutobahnCpp. You can also run components that are not connected to your application via WAMP (an example for this would be an image processor which just watches a directory and converts images as they come in so that they can be used by the application).

Control and integration here is limited to what can be achieved using standard system mechanisms.

#### Router Worker

A router worker mainly routes WAMP application traffic, but can also host Python/Twisted application components.

##### Creating

You create a router worker on a specific node by doing

```console
cdc create router <full_router_id> <router_config>
```

The <full_router_id> is the fully qualified path which is required to address the router worker, i.e. a combination of the <node_id> and a <router_id>, e.g.

```console
cdc create router mynode1.router66
```

where the <router_id> needs to be unique within the node.

If just the <node_id> is given, the then CDC backend assigns a unique ID.

The <router_config> is a JSON data structure which contains the configuration options for the router, e.g.

--- add router config example ---

If no <router_config> is given, then the router starts up as a shell without the possibility for clients to connect. The necessary configuration can then be done in parts (see Realms and Transports below).

Creating a router worker creates an entry in the CDC database. It does not start up the router.

##### Starting

To start a router based on an entry in the CDC database, do

```console
cdc start router <full_router_id>
```

where the <full_router_id> consists of a <node_id> and a <router_id>, e.g.

```console
cdc start router mynode1.router66
```

##### Stopping

To stop a running router do

```console
cdc stop router <full_router_id>
```

where the <full_router_id> consists of a <node_id> and a <router_id>, e.g.

```console
cdc stop router mynode1.router66
```

##### Modifying

To modify the configuration of an existing router worker, do

```console
cdc modify router <full_router_id> <change_set>
```

where the <full_router_id> consists of a <node_id> and a <router_id>.

The <change_set> is required and can be a full replacement for the current router configuration, or contain one or more of options, realms, transports and components. Each of these subsets replaces the current set in the configuration in its entirety. For more fine-grained modifications of realms or transports, see the respective sections below.

Modifying a router worker modifies the entry for that worker in the CDC database. These changes do not directly affect a running worker. They will be applied on a restart or a relaunch.

##### Reloading

Changes to a router modification are naturally applied on a restart, and a restart is indeed required for some modifications to take effect. Other modifications may, however, be applied without this. To use this possibility, do

```console
cdc reload router <full_router_id> restart='true'
```

This checks whether the current modifications to the router configuration can be applied without a restart of the router. If this is the case, then the changes are applied.

If the changes require a restart, then the outcome is determined by the `restart`argument. If this is set to `true`, the router is restarted, if `false` then the changes in their entirety are not applied.

##### Deleting

To delete a router, do

```console
cdc delete router <full_router_id>
```

This deletes the router's entry from the CDC database. If the router is currently running, it stops the router before the deletion of the database entry.

##### Realms

WAMP routing occurs within realms, i.e. messages are only routed between client sessions connected to the same realm. In order for a router worker to do application routing, at least one realm needs to be configured.

   * Creating

   To create a realm, do

   ```console
   cdc create realm <full_realm_path> <realm_config>
   ```

   where full realm path comprises <node_id>, <router_id> and <realm_id>. The <realm_id> must be unique within the scope of the router. If no <realm_id> is given, then the CDC backend creates one.

   As an example

   ```console
   cdc create realm mynode1.router66.realm1
   ```

   The <realm_config> is a JSON data structure containing the roles and their permissions defined on the realm. If no <realm_config> is given, then the realm is created as a shell, and no connections to the realm are possible until at least one role has been defined for the realm (see below).

   --- add sample realm config ---

   The creation of a realm creates an entry in the CDC database. It does not start the realm.

   * Starting

   To start a realm do

   ```console
   cdc start realm <full_realm_path>
   ```

   * Stopping

   To stop a realm do

   ```console
   cdc stop realm <full_realm_path>
   ```

   * Modifying

   To modify a realm do

   ```console
   cdc modify realm <full_realm_path> <change_set>
   ```

   where the <change_set> is either a full realm configuration, a change in the name of the realm, or a set of roles which replaces the current set. If you want to add, remove or modify permissions or roles, use the more specific mechanisms described further below.

   * Reloading

? is there a reloading? The realm is not something which runs, but which exists on the router. It is always possible to change this without a restart of the router. adding roles is always possible without affecting anything currently running, while removing roles would kill connections. The question here is not 'restart' but 'apply if this affects current connections' ???


   * Deleting

   To delete a realm do

   ```console
   cdc delete realm <full_realm_path>
   ```

   This deletes the realm from the CDC database. If the realm is currently running, it stops the realm before the deletion.


? does the CLI allow the control of roles and permissions, or do we end this at the realm level ?

##### Transports

Realms are what WAMP clients connect to logically, transports are how they connect technically. To fulfill its function, a router worker requires at least one transport. For the different types of transports and the available options see the Crossbar.io documentation.

   * Creating a Transport

   To create a transport, do

   ```console
   cdc create transport <full_transport_path> <transport_config>
   ```

   where the <full_transport_path> is consists of <node_id>, <router_id>, <realm_id> and <transport_id>, e.g.

   ```console
   cdc create transport mynode1.router66.realm1.transport2
   ```

   The <transport_id> must be unique within the realm. If no <transport_id> is given, the CDC backend creates one.

   The <transport_config> is required and is a JSON data structure, e.g.

   --- add transport config example ---

   Creating a transport creates an entry in the CDC database. It does not start the transport.

   * Starting a Transport

   To start a transport do

   ```console
   cdc start transport <full_transport_path>

   * Stopping a Transport

   To stop a transport do

   ```console
   cdc stop transport <full_transport_path>

   * Modifying a Transport

   To modify a transport do

   ```console
   cdc modify transport <full_transport_path> <change_set>
   ```

   where the <change_set> is either a full transport configuration, a change in the name of the transport, or a set of the remaining configuration options which replaces the current set.

   Modifying a transport modifies the entry in the CDC database, but these changes are not applied to a running transport.

   * Reloading a Transport

   To reload a transport do

   ```console
   cdc reload transport <full_transport_path> --restart='true'
   ```

   This checks whether the current modifications to the transport configuration can be applied without a restart of the transport. If this is the case, then the changes are applied.

   If the changes require a restart, then the outcome is determined by the `restart`argument. If this is set to `true`, the transport is restarted, if `false` then the changes in their entirety are not applied.

   * Deleting a Transport

   To delete a transport do

   ```console
   cdc delete transport <full_transport_path>
   ```

   This deletes the transport from the CDC database. If the transport is currently running, it stops the transport before the deletion.

##### Components

In addition to the router functionality, a router worker can host Python/Twisted application components. These run in the same process as the router worker.

   * Creating a Component
   * Starting a Component
   * Stopping a Component
   * Modifying a Component
   * Reloading a Component
   * Deleting a Component


#### Container Worker

Container workers can host Python/Twisted application components. All components hosted within a container run within the same system process. Since multiple containers can run on separate cores, containers allow scale-up on a machine running a node. Since there is no need for containers to run within the same node as a router they connect to, WAMP applications running in containers can also scale out.

##### Creating a Container Worker



##### Starting a Container Worker



##### Stopping a Container Worker



##### Modifying a Container Worker



##### Relaunching a Container Worker



##### Deleting a Container Worker



#### Transports




#### Guest Worker

Guest workers offer the possibility to host application components for any available runtime in Crossbar.io.


##### Creating a Guest Worker



##### Starting a Guest Worker



##### Stopping a Guest Worker



##### Modifying a Guest Worker



##### Relaunching a Guest Worker



##### Deleting a Guest Worker







## Monitoring

'cdc' enables the monitoring of nodes or components running in a node, e.g. the CPU usage or network traffic, the addition of workers and changes to permissions.

main use cases:

- admin wants to check on the health: components running, CPU usage, network usage etc.
- admin wants to check on a problem: get the log of a node or worker
- developer wants to debug an application: get the log of a node, but more likely worker, transport, traffic for a role, URI

Output would be simple, e.g. a new line with CPU usage added once a second, log lines getting printed as the logging occurs in the CDC.

We do not offer the dynamic monitoring, e.g. for realms being added, that the Web UI does.


### Listing nodes

To list all nodes configured in the management realm connected to (whether the node is çurrently running or not):

```console
cdc list nodes
```

To list only running nodes:

```console
cdc list nodes --filter_running
```

To list nodes using JSON as output format:

```console
cdc list nodes --output=json
```

### Listing workers

To list all workers configured on the given node (whether the worker is currently running or not)

```console
cdc list workers mynode
```

To list only workers which are currently running

```console
cdc list workers mynode --filter_running
```

To list workers using JSON as output format:

```console
cdc list workers mynode --output=json
```

### Getting logs

`cdc` allows to remotely tap into the live log stream produced by Crossbar.io nodes and node workers.

E.g. when running a guest or container worker that hosts WAMP application components, you might want to get access to log messages produced by such components.

Features:

- Tail the node log
- Tail a specific worker log
- Get the (complete) current node log
- Get an archived node log
- Filter by loglevel (only return stuff >= given loglevel)

Open questions:

- Tail (obviously) only works for nodes and workers currently running
- Get log _might_ also work when the node/worker is offline if we perstist the logs in the service database - OPEN

Possible command syntax (DRAFT):

```console
cdc tail log  log mynode.myworker
```


```console
cdc get log mynode.myworker
```

```console
cdc log worker mynode.myworker
```

```console
cdc log worker mynode.myworker --tail=100
```

```console
cdc log worker mynode.myworker --
```


