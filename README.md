# Digging into Data: Mining relationships among variables in large datasets from complex systems

### Developer Linux Setup
- install virtualenv via `pip install virtualenv` or via  Linux package manager, e.g, `apt-get install python-virtualenv virtualenvwrapper`
- create a virtualenv via `virtualenv miracle` (or `mkvirtualenv miracle` if using virtualenvwrapper which provides
  aliases for manipulating virtualenvs, `mkvirtualenv <virtualenv-name>` and `workon <virtualenv-name>`)
- run `pip install -U pip` inside your virtualenv (avoids a bug in Ubuntu's packaged pip, may now be fixed)
- run `pip install -Ur requirements.txt` to install Python dependencies. Add any additional python dependencies to this
  file, preferably with frozen version numbers
- copy and customize the `local.py` settings file, e.g., `% cp miracle/settings/local.py.example miracle/settings/local.py`

### Setup the databases
- If you have `trust` permissions setup in your `pg_hba.conf` file, `fab setup` will setup and initialize the database. 
  Otherwise, create the postgres databases `miracle_metadata` and `miracle_data` and the `miracle` postgres user
  manually and then run `fab initdb` to initialize and create the schema.
- **NOTE:** Schema is still evolving. Run `fab rebuild_schema` to drop the database, delete any generated migrations, and
  rebuild the schema. If you have local data that you'd like to preserve, use `dumpdata` or use `makemigrations` and
  `migrate` to try to migrate it to the new schema.
  
### load test data
Data fixtures in `miracle/core/fixtures` can be loaded via `%./manage.py loaddata <fixture-name-without-file-extension>`. 


### Codebase Status
[![Build Status](https://travis-ci.org/comses/miracle.svg?branch=master)](https://travis-ci.org/comses/miracle)
[![Coverage Status](https://coveralls.io/repos/comses/miracle/badge.svg)](https://coveralls.io/r/comses/miracle)
[![Code Health](https://landscape.io/github/comses/miracle/master/landscape.svg?style=flat)](https://landscape.io/github/comses/miracle/master)
