# Digging into Data: Mining Relationship Among Variables in Large Datasets from Complex Systems

### Developer Setup

Steps to set up a development environment:

- install virtualenv via `pip install virtualenv` or via a Linux package manager, e.g, `apt-get install python-virtualenv virtualenvwrapper`
- create your virtualenv via `virtualenv miracle` or `mkvirtualenv miracle` if you're using virtualenvwrapper, which
  provides convenient aliases for manipulating virtualenvs:  `mkvirtualenv <virtualenv-name>` and `workon <virtualenv-name>`
- run `pip install -U pip` inside your virtualenv (avoid a bug in Ubuntu's packaged pip, may now be fixed)
- run `pip install -Ur requirements.txt` to install Python dependencies. Anytime we pull in additional frameworks or
  dependencies, add them to this file
- customize the `local.py` settings file, `cp miracle/settings/local.py.example miracle/settings/local.py`
- If you have `trust` permissions setup in your `pg_hba.conf` file, `fab setup` will setup and initialize the database. 
  Otherwise, create the postgres databases and users manually and then run `fab initdb` to initialize and create the
  schema.
- If the schema changes you can always rerun `fab rebuild_schema` to drop the database, delete any generated migrations,
  and rebuild the schema. This will destroy all data however.


### Codebase Status
[![Build Status](https://travis-ci.org/comses/miracle.svg?branch=master)](https://travis-ci.org/comses/miracle)
[![Coverage Status](https://coveralls.io/repos/comses/miracle/badge.svg)](https://coveralls.io/r/comses/miracle)
[![Code Health](https://landscape.io/github/comses/miracle/master/landscape.svg?style=flat)](https://landscape.io/github/comses/miracle/master)
