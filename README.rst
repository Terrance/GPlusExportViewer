Google+ Export Viewer
=====================

A small webapp for rendering exports from Friends+Me's `Google+ Exporter`_.

.. _Google+ Exporter: https://gplus-exporter.friendsplus.me

Requires Python with the ``flask`` package installed.

Basic viewer
------------

Place JSON format exports in the *data* directory.

Run ``viewer.py`` and open http://localhost:5000 to choose an export file.

Proxy
-----

Set environment variable ``GPEV_DATA`` to the path of a combined export file.

Run ``proxy.py`` and open http://localhost:5000 for a list of supported URLs.
