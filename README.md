# dockbot
A continuous integration system which uses Docker and Buildbot.  Dockbot is a
Python program which starts a **master** Docker instance and a number of
build **slaves**.  The **master** coordinates builds, offers a Web interface
for monitoring and controlling builds and triggers builds based on changes
to source repositories.  The **slaves** perform the builds under different
configurations.

# Installation
You can install dockbot as follows:

    git clone https://github.com/CauldronDevelopmentLLC/dockbot
    cd dockbot
    sudo python setup.py install

# Overview
To use dockbot you need to create a ``dockbot.json`` configuration file in a
directory of it's own and a number of **slaves** in a directory called
``slaves``.  In the slave directories you also have ``dockbot.json`` files
which configure which projects the slave will run.  The directory structure
should look like this:

    dockbot.json
    lib/
    slaves/
      slave1/
        dockbot.json
        projectA.docker
        projectB.docker
        ...
      slave2/
        ...
      slaveN/
        ...

The optional ``lib`` directory can contain Docker file fragments which may be
used by multiple slaves.

# Basic configuration
The top level ``dockbot.json`` file needs a some basic configuration
information to setup the dockbot install:

```
"project": "Dockbot",
"url": "https://github.com/CauldronDevelopmentLLC/dockbot",
"namespace": "dockbot",
"admin": "Joseph Coffland <jcoffland@cauldrondevelopment.com>",
"ip": "127.0.0.1",
"http-port": 8049,
"buildbot-port": 8050,
```

These configuration values have the following meanings:

 * project - The dockbot project name.
 * url - The project URL, cosmetic only.
 * namespace - A unique name prefix for docker images in this project.
 * admin - A email address, cosmetic only.
 * ip - The IP address to which ports should be bound.
 * http-port - The HTTP port for the build master's Web interface.
 * buildbot-port - Opening this port allows other build slaves to connect.


# Build modes
Often software can be built in more than one way.  Build modes make it possible
to configure different builds configurations for the same software.  Build mode
configuration looks like this:

```
"modes": {
  "debug": {"scons": {"debug": 1}},
  "release": {}
},
```

Above we configure two build modes ``debug`` and ``release``.  The names are
arbitrary and can be anything you like.  The dictionaries under these names
override options specific to those moves.

# Projects
```
"projects": {
  "_default_": {
    "compile": ["scons", "-k"],
  },

  "cbang": {
    "test": true,
    "repo": {
      "type": "git",
      "url": "https://github.com/CauldronDevelopmentLLC/cbang",
      "branch": "master"
    }
  }
}
```

The ``projects`` section is a dictionary of project configurations.  The special
``_default_`` section sets the default configuration options for all projects.
Project names are arbitrary and may contain the following configuration options:

  * compile - The compile command.
  * test - If true testing should be performed after the build is complete
  * repo - The source repository configuration
    * type - One of ``git``, ``github`` or ``svn``
    * url - The repository url.
    * org - An organization, used only with ``github`` repos with out a ``url``.
    * user - The repo user name.
    * pass - The repo password, if needed.
    * branch - The repository branch.
  * deps - Projects which must be built first.
  * packages - A list of package types, appended to the compile command.
  * build - If false the build step is omitted.

# Slaves
A slave represents a particular build configuration.  Each slave has its own
directory under ``slaves``.  The ``dockbot.json`` file in this directory defines
one or more images that will be built and adds any extra configuration options
particular to the slave.

# Slave images
A slave image is a Docker image which will be run in one or more **modes**.
Images are defined in the slave's ``dockbot.json`` as follows:

```
"images": {
  "cbang": {"projects": ["cbang"]}
}
```

In the above example one image ``cbang`` is defined with one project ``cbang``.
The project must be defined in the top level ``dockbot.json``.  To build the
image dockbot will look for a file ``cbang.docker`` in the slave's directory.
It will then process this file with ``m4`` to produce a final ``Dockerfile``
used to build the image.  The ``m4`` preprocessor will combine Dockerfile
fragments to create the complete ``Dockerfile``.  These fragments may exist
either in the slave's own directory, in a top level ``lib`` directory or in
the dockbot default libs.

An example project ``.docker`` file make look like this:

```
include(base.m4)
include(slave.m4)
```

``base.m4`` is defined as:

```
FROM debian:testing

include(debian.m4)
include(boost-1.59.0.m4)
include(buildbot.m4)
include(debian-gcc-4.8.m4)
```

Each of these ``include()`` lines references a docker file fragment located in
one of the lib directories.

# Building dockbot images
To build a dockbot image run the following command:

    dockbot build <image>

Where ``<image>`` is the name of the image.  e.g.
``dockbot-debian-testing-64bit-cbang``.  If the image is successfully build then
it can be started.

To rebuild a dockbot image run the following:

    dockbot rebuild <image>

This command first deletes the old build than builds it again applying any
configuration changes.  In order to do a rebuild all of the images's containers
must first be stopped.

# Starting & running the build master
The build master is a special docker container which coordinates the builds.
Like the slaves it too must be built and run.  This is accomplished as follows:

    dockbot build master
    dockbot start master

The build master must be restarted whenever the dockbot configuration is
changed.  To stop the master run the following:

    dockbot stop master

# Dockbot status
To view the status of the dockbot containers run the following:

    dockbot status

or simply:

    dockbot

This will list the status of all configured dockbot containers.  To check the
status of a particular dockbot container run:

    dockbot status <container>

You can also view the complete configuration of a dockbot container like this:

    dockbot config <container>

# Opening a shell in a running instance
Some times it is desirable to login and inspect the contents of a container.
This is a accomplished with the dockbot ``shell`` command:

    dockbot shell <container>

If the image was previously built this will open a shell in the container.  If
the container was already running it will attach a new shell to the running
container.

# The Web interface
The build master's Web interface makes it possible to monitor and control
builds.  To view the Web interface navigate a brower to the IP and port
specified in the top level ``dockbot.json`` file.  At least the build master
container must be running.  Some slave containers should also be running to
make it useful.

# Triggering builds
Builds may be manually triggered by opening the build master's Web page in a
browser and clicking on a project name in the third row, then clicking the
``Force Build`` button.  Normally bulids are automatically triggered by changes
in the source repository.  Source repository change notifications must be
configured on the repository side.

# Triggering builds from GitHub
TBD

# Publishing builds
The last 5 completed builds are placed in ``run/buildmaster/builds/``.  Once all
the builds for a particular project are correct they can be published using
the ``dockbot-publish`` tool.

# Publishing builds to GitHub
