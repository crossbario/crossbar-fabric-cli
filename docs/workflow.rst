Workflows
=========

1. Developer scaffolds a XBR API project

    cbsh quickstart api

This collects information such as:

    <project>
    <api_author>
    <api_license>
    <uri_namespace>
    ...

The collected information is used to gernate the following files:

    README
    LICENSE
    package.json
    schema.fbs
    index.rst

and two (empty) subdirectories for more FlatBuffer and ReST files
to be included from the main schema.bfs and index.rst files:

    include/..      # .fbs include files (optional)
    docs/..         # .rst include files (optinal)

2. Developer fills in his API, editing above files, optionally adding more.

3. Developer compiles the API project

    cbsh bundle api

This checks (via embedded flatc compiler and embedded Sphinx)
that all files are valid and creates a file archive,
an API package:

    <project>.zip


3. Developer imports the API package into local design repository:

    cbsh import api

3.1 Load Schema data

Next, the LSP server, notified of the filesystem change on the path

    $HOME/.cbsh/api/schema

will 



3.2 Generate API documentation

This loads the (parsed) content of files from the archive:

    package.json
    index.rst
    docs/..

into files/directories in

    $HOME/.cbsh/api/docs/<project>/

and inserts a reference to

    $HOME/.cbsh/api/docs/<project>/index.rst

into

    $HOME/.cbsh/api/docs/index.rst

Next, the embedded Sphinx with our Sphinx extension to render the .rst files

    $HOME/.cbsh/api/docs

to HTML files in

    $HOME/.cbsh/api/docs/_build

The Spinx extension is written in Python, and accesses the schema data in LMDB to resolve
references to FlatBuffer definitions.



5. Developer publishes the API library

    cbsh publish api
