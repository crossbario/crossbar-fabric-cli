FROM python:3.5

MAINTAINER The Crossbar.io Project <support@crossbario.com>

ENV DEBIAN_FRONTEND noninteractive

RUN pip install pyinstaller

RUN mkdir /build
WORKDIR /build

COPY ./dist/cbsh-*.tar.gz /build
RUN pip install cbsh-*.tar.gz

# this builds /build/dist/cbsh
COPY cbsh/ /build/cbsh/
RUN pyinstaller --onefile --name cbsh cbsh/cli.py
