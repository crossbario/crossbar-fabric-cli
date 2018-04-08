# Crossbar.io Fabric Shell


Installation:

python3 -m venv ~/cbsh
source ~/cbsh/bin/activate
pip install cbsh
cbsh version

Add ${HOME}/cbsh/bin to your PATH

Update:

pip install --no-cache --upgrade cbsh





Interactive shell to access Crossbar.io Fabric Center and manage your Crossbar.io Fabric nodes from the command line.

## Installation

Crossbar.io Fabric Shell is [available from PyPI](https://pypi.python.org/pypi/cbsh) and requires Python 3.5 or higher.

We recommend installation into a dedicated Python [virtualenv](https://virtualenv.pypa.io/en/stable/):

```console
virtualenv venv
source venv/bin/activate
pip install cbsh
```

A straigforward way to install into a shared directory outside your personal user HOME is installing into `/opt/cbsh` by creating a virtualenv:

```console
sudo virtualenv -p /usr/bin/python3 /opt/cbsh
sudo /opt/cbsh/bin/pip3 install cbsh
```

To test the installation:

```consoleb
(cpy361_12) oberstet@thinkpad-t430s:~$ cbsh version
Crossbar.io Fabric Shell 17.7.1
```

## Usage

### Registering

> Note: if you are running a local CFC, please see [Using a local CFC](#using-a-local-cfc)).

To use Crossbar.io Fabric Shell with Crossbar.io Fabric Center, the first thing to do is to register or login as a user:

```console
cbsh auth
```

If you haven't run this before, you will be asked for your email address:

```console
(cpy362_3) oberstet@thinkpad-t430s:~$ cbsh version
Crossbar.io Fabric Shell 17.9.1
(cpy362_3) oberstet@thinkpad-t430s:~$ cbsh
Crossbar.io Fabric Shell: v17.9.1
Created new local user directory: /home/oberstet/.cbf
Crossbar.io Fabric Center URL [wss://fabric.crossbario.com/ws]:
Created new local user configuration: /home/oberstet/.cbf/config.ini
Active user profile: default
Please enter your email address: tobias.oberstein@gmail.com
We will send an activation code to tobias.oberstein@gmail.com, ok? [Y/n]:
New user public key generated: /home/oberstet/.cbf/default.pub
New user private key generated (keep this safe!): /home/oberstet/.cbf/default.priv
Connecting to wss://fabric.crossbario.com/ws ..
Entering event loop ..

Thanks for registering! We have sent an authentication code to tobias.oberstein@gmail.com.
Please check your inbox and run "cbsh auth --code <THE CODE YOU GOT BY EMAIL>.
```

You should now receive an email with an activation code, eg `RESF-MQPJ-WPYQ`. To use that code:

```console
cbsh auth --code RESF-MQPJ-WPYQ
```

When activation was successful, as short notice with your session details will be shown:


```console
(cpy362_3) oberstet@thinkpad-t430s:~$ cbsh auth --code RESF-MQPJ-WPYQ
Crossbar.io Fabric Shell: v17.9.1
Active user profile: default
User public key loaded: /home/oberstet/.cbf/default.pub
User private key loaded: /home/oberstet/.cbf/default.priv
Connecting to wss://fabric.crossbario.com/ws ..
Entering event loop ..

    Welcome to Crossbar.io Fabric Shell v17.9.1

    Press Ctrl-C to cancel the current command, and Ctrl-D to exit the shell.
    Type "help" to get help. Try TAB for auto-completion.

    Connection:

        url         : wss://fabric.crossbario.com/ws
        authmethod  : cryptosign
        realm       : com.crossbario.fabric
        authid      : tobias.oberstein@gmail.com
        authrole    : user
        session     : 6186592563885360

```

Your client is now all setup. A public/private key pair as well as a configuration file for CBSH was generated:

```console
(cpy361_12) oberstet@thinkpad-t430s:~$ ls -la ~/.cbf/
insgesamt 20
drwxrwxr-x  2 oberstet oberstet 4096 Aug  5 15:45 .
drwxr-xr-x 95 oberstet oberstet 4096 Aug  7 16:16 ..
-rw-rw-r--  1 oberstet oberstet   78 Aug  5 15:46 config.ini
-rw-------  1 oberstet oberstet  332 Aug  5 15:45 default.priv
-rw-r--r--  1 oberstet oberstet  227 Aug  5 15:45 default.pub
```

You can now start CBSH just by typing:

```console
cbsh
```

CBSH will connect and present an interactive REPL loop:

```

    Welcome to Crossbar.io Fabric Shell v17.9.1

    Press Ctrl-C to cancel the current command, and Ctrl-D to exit the shell.
    Type "help" to get help. Try TAB for auto-completion.

    Connection:

        url         : wss://fabric.crossbario.com/ws
        authmethod  : cryptosign
        realm       : com.crossbario.fabric
        authid      : tobias.oberstein@gmail.com
        authrole    : user
        session     : 5159216761637739

>>
```

---


### Using a local CFC

When running CFC on-premise (for OEMs), you will need to configure your CFC listening URL in `~/.cbf/config.ini`, eg:

```
[default]

url=ws://localhost:9000/ws
privkey=default.priv
pubkey=default.pub
```

You can specify a custom CFC URL during the first run of `cbsh`:

```console
Crossbar.io Fabric Shell: v17.7.1
Created new local user directory: /home/oberstet/.cbf
Crossbar.io Fabric Center URL [wss://fabric.crossbario.com]: ws://localhost:9000/ws
Created new local user configuration: /home/oberstet/.cbf/config.ini
Active user profile: default
Please enter your email address: tobias.oberstein@gmail.com
We will send an activation code to tobias.oberstein@gmail.com, ok? [Y/n]:
New user public key generated: /home/oberstet/.cbf/default.pub
New user private key generated (keep this safe!): /home/oberstet/.cbf/default.priv
Connecting to ws://localhost:9000/ws ..
Entering event loop ..

Thanks for registering! We have sent an authentication code to tobias.oberstein@gmail.com.
Please check your inbox and run "cbsh auth --code <THE CODE YOU GOT BY EMAIL>.
```

When the OEM CFC was configured including Mailgun connection, you will receive an email with an activation code.

When the OEM CFC lacks Mailgun configuration, the authentication code will instead be printed in the CFC log:

```
cfc1_1   | 2017-08-09T14:50:35+0000 [Router         18] Mailgun not configured! This is the mail that would have been sent: {"from": "Crossbar.io <no-reply@mailing.crossbar.io>", "to": ["tobias.oberstein@gmail.com"], "subject": "Crossbar.io Fabric: your REGISTRATION code", "text": "We have received a registration request for your account. Please use this activation code: 7M46-7XWT-GA9P"}
```

In both cases, activation then works like this:


```console
(cpy361_10) oberstet@thinkpad-t430s:$ cbsh auth --code 7M46-7XWT-GA9P
Crossbar.io Fabric Shell: v17.7.1
Active user profile: default
User public key loaded: /home/oberstet/.cbf/default.pub
User private key loaded: /home/oberstet/.cbf/default.priv
Connecting to ws://localhost:9000/ws ..
Entering event loop ..

    Welcome to Crossbar.io Fabric Shell v17.7.1

    Press Ctrl-C to cancel the current command, and Ctrl-D to exit the shell.
    Type "help" to get help. Try TAB for auto-completion.

    Connection:

        url         : ws://localhost:9000/ws
        authmethod  : cryptosign
        realm       : com.crossbario.fabric
        authid      : tobias.oberstein@gmail.com
        authrole    : user
        session     : 7988562296859153

```

---

