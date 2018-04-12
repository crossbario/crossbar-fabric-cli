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

import os
import uuid
import six

import click
import yaml
from cookiecutter.main import cookiecutter

from autobahn import util

README = """# Crossbar.io Quickstart Project

This project was generated using quickstart templates for Crossbar.io based services.

The services are [Docker](https://www.docker.com/) based, and the service bundling is
using [Docker Compose](https://docs.docker.com/compose/).

To build your services:

```console
make build
```

To check the service versions:

```console
make version
```

To start your services:

```console
make start
```

> Note: the latter is simply starting all services with `docker-compose up`. To start
the services in the background, type `docker-compose up --detach`.
"""

MAKEFILE = """
SUBDIRS = $(shell ls -d */)

default: start

version:
\tfor dir in $(SUBDIRS) ; do \
\t\techo "$$dir" ; \
\t\tcat $$dir/service.json ; \
\t\tmake -C  $$dir version ; \
\tdone

build:
\tdocker-compose build

# the following will automatically build the images from the Dockerfiles
# references in docker-compose.yml, and it will also rebuild those images
# and recreate containers as needed (eg when the Dockerfile or again a file
# referenced therein, such as your actual application source code files, changes)
#
start:
\tdocker-compose up --build
"""

DEVMODE = True

if DEVMODE:
    CC1 = '/home/oberstet/scm/crossbario'
    CC2 = '/home/oberstet/scm/xbr'
else:
    CC1 = 'gh:crossbario'
    CC2 = 'gh:xbr'


# built-in cookiecutters.
#
_cookiecutters = [
    # Crossbar.io
    (None, 'Crossbar.io'),
    ('{}/cookiecutter-crossbar'.format(CC1), 'Create a Crossbar.io OSS app router'),
    ('{}/cookiecutter-crossbar-fabric'.format(CC1), 'Create a Crossbar.io Fabric app router'),
    ('{}/cookiecutter-crossbar-fabric-center'.format(CC1), 'Create a Crossbar.io Fabric cluster controller'),

    # XBR
    (None, 'XBR'),
    ('{}/cookiecutter-xbr-api'.format(CC2), 'Create a XBR API bundle'),
    ('{}/cookiecutter-crossbar-fabric-xbr'.format(CC1), 'Create a Crossbar.io XBR data market'),

    # Autobahn
    (None, 'Autobahn'),
    ('{}/cookiecutter-autobahn-python'.format(CC1), 'Create a Python based app or XBR service'),
    ('{}/cookiecutter-autobahn-js'.format(CC1), 'Create a JavaScript based app or XBR service'),
    ('{}/cookiecutter-autobahn-java'.format(CC1), 'Create a Java based app or XBR service'),
    ('{}/cookiecutter-autobahn-cpp'.format(CC1), 'Create a C++ based app or XBR service'),
]


def hl(text):
    if type(text) != six.text_type:
        text = '{}'.format(text)
    return click.style(text, fg='yellow', bold=True)


def run(cfg):
    click.echo('\n{cb} Project Quickstart\n'.format(cb=hl('Crossbar.io / XBR')))

    _templates = {}

    num = 0
    click.echo('  {}: Exit'.format(hl(num)))

    for template, desc in _cookiecutters:
        if template:
            num += 1
            _templates[num] = template
            template_disp = hl(template)
            click.echo('  {num}: {desc:46s} [{template}]'.format(num=hl(num), desc=desc, template=template_disp))
        else:
            click.echo('\n {}:\n'.format(hl(desc)))
    click.echo('')

    select = None
    while select not in range(0, num + 1):
        select = click.prompt('Please select', type=int, default=0)

    if select > 0:
        template = _templates[select]
        click.echo('Initializing cookiecutter {} ...'.format(template))

        extra_context = {
            'uid': os.getuid(),
            'service_uuid': str(uuid.uuid4()),
            'generated': util.utcnow(),
        }
        output_dir='.'

        # cookiecutter returns the fully qualified path within which the template
        # was initialized.
        output_dir = cookiecutter(template, output_dir=output_dir, extra_context=extra_context)

        # the last part of the fully qualified output directory is the service name
        # that comes from "cookiecutter.json"
        service_name = os.path.basename(output_dir)

        readme_filename = 'README.md'
        if not os.path.isfile(readme_filename):
            with open(readme_filename, 'w') as fd:
                fd.write(README)
            click.echo('{} created'.format(readme_filename))

        makefile_filename = 'Makefile'
        if not os.path.isfile(makefile_filename):
            with open(makefile_filename, 'w') as fd:
                fd.write(MAKEFILE)
            click.echo('{} created'.format(makefile_filename))

        docker_compose_filename = 'docker-compose.yml'
        if not os.path.isfile(docker_compose_filename):
            docker_compose = {
                'version': '3',
                'services': {}
            }
            with open(docker_compose_filename, 'w') as fd:
                fd.write(yaml.safe_dump(docker_compose))
            click.echo('{} created'.format(docker_compose_filename))

        docker_compose = None
        with open(docker_compose_filename) as fd:
            data = fd.read()
            docker_compose = yaml.safe_load(data)

        if type(docker_compose) != dict:
            click.error('invalid type {} found in {} for top level object'.format(type(docker_compose), docker_compose_filename))

        if 'services' not in docker_compose:
            docker_compose['services'] = {}

        # we expect the cookiecutter to produce a docker-compose-<service_name>.yml file
        service_docker_compose_filename = os.path.join(output_dir, 'docker-compose-{}.yml'.format(service_name))

        if not os.path.isfile(service_docker_compose_filename):
            click.error('docker-compose fragment for service was not generated by cookiecutter. missing file:\n{}'.format(service_docker_compose_filename))

        service_docker_compose = None
        with open(service_docker_compose_filename) as fd:
            data = fd.read()
            service_docker_compose = yaml.safe_load(data)

        if service_name in docker_compose['services']:
            click.echo('updating service "{}" existing in docker-compose.yml'.format(service_name))
        else:
            click.echo('adding service "{}" to docker-compose.yml'.format(service_name))

        docker_compose['services'][service_name] = service_docker_compose

        with open(docker_compose_filename, 'w') as fd:
            fd.write(yaml.safe_dump(docker_compose))
        click.echo('{} written'.format(docker_compose_filename))
