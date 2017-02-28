FROM python:3.5

MAINTAINER The Crossbar.io Project <support@crossbario.com>

ENV DEBIAN_FRONTEND noninteractive

RUN pip install pyinstaller

RUN mkdir /build
WORKDIR /build

RUN pip install https://s3-eu-west-1.amazonaws.com/fabric-deploy/autobahn/autobahn-0.17.2-py2.py3-none-any.whl

COPY ./dist/crossbarfabriccli-0.1.0.tar.gz /build
RUN pip install crossbarfabriccli-0.1.0.tar.gz

# this builds /build/dist/cbsh
COPY crossbarfabriccli/ /build/crossbarfabriccli/
RUN pyinstaller --onefile --name cbsh crossbarfabriccli/cli.py
