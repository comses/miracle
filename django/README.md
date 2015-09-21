# Digging into Data: Mining relationships among variables in large datasets from complex systems

### Developer Linux Setup
- install [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) using pip or other package manager, e.g, `% apt-get install python-virtualenv virtualenvwrapper`
- create a virtualenv: if using virtualenvwrapper, `% mkvirtualenv miracle` to create the virtualenv and `% workon miracle` to activate it, if using `virtualenvwrapper`
- `% pip install -Ur requirements.txt` to install all Python dependencies. Add python dependencies to this file,
  preferably with frozen version numbers
- use [nodeenv](https://pypi.python.org/pypi/nodeenv), e.g., `% nodeenv -p` to set up an isolated nodejs environment
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

Projects can be loaded from the command line using `manage.py load_project`. To load a project using testuser0:

```
./manage.py load_project --creator testuser0 --group-file "path/to/groupfile.yml" "path/to/archive"
```

Groupfiles for the luxe and DID_UT_RHEA projects are included in the `test_archive/` directory. If `luxe.7z` were in
the `test_archive` directory it could be loaded by running

```
./manage.py load_project --creator testuser0 --group-file "/opt/miracle/tmp/luxe.miracle.yml" "/opt/miracle/tmp/luxe.7z"
```

### Codebase Status
[![Build Status](https://travis-ci.org/comses/miracle.svg?branch=master)](https://travis-ci.org/comses/miracle)
[![Coverage Status](https://coveralls.io/repos/comses/miracle/badge.svg)](https://coveralls.io/r/comses/miracle)
[![Code Health](https://landscape.io/github/comses/miracle/master/landscape.svg?style=flat)](https://landscape.io/github/comses/miracle/master)
