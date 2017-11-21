Setting up regolith
-------------------

Regolith requires at least one git repository which contains the research group
database.
The database repository contains the various databases that regolith manages
and a ``regolithrc.json`` file.

The ``regolithrc`` file
===================

The regolithrc file controls regolith's operations, telling it where to look
for your data and where to deploy your website. Here is an example file,

.. code-block:: json

        {"groupname": "BillingeGroup",
         "databases": [
          {"name": "billingegroup-public",
           "url": "http://github.com/billingegroup/rg-db-public.git",
           "public": true,
           "path": "db"}
         ],
          ]
        }


The database repo(s)
====================

You will nead at least one database repo to use regolith.
You will need to create
