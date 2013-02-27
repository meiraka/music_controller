===============
MusicController
===============

MusicController is a Pretty client for MusicPlayerDaemon.

REQUIREMENTS
============
  python 2.6 or 2.7
  wxPython (tested with wxGTK and wxMac (cocoa))

INSTALL
=======

::

  python setup.py install

RUNNING
=======

::

  music-controller

or run in source dir:

::

  ./music-controller

BUILD PACKAGE
=============

debian
------

::
  $ sudo apt-get install debscripts debhelper cdbs coreutils hostname mercurial \
  python python-central python-setuptools python-docutils python-mpd
  $ debuild -us -uc -I

Mac OSX
-------

::
  python setup.py py2app

:AUTHOR:
  mei raka

:LICENSE:
  GPLv3


