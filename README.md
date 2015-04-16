# Digging into Data: Mining Relationship Among Variables in Large Datasets from Complex Systems

### Developer Documentation

Steps to set up a development environment:

- install virtualenv via `pip install virtualenv` or via a Linux package manager, e.g, `apt-get install python-virtualenv virtualenvwrapper`
- create your virtualenv via `virtualenv miracle` or `mkvirtualenv miracle` if you're using virtualenvwrapper, which is great and provides `mkvirtualenv <virtualenv-name>` and `workon <virtualenv-name>` aliases
- run a `pip install -U pip` inside your virtualenv to avoid bugs in Ubuntu's packaged version of pip
- run `pip install -Ur requirements.txt` to install Python dependencies - anytime we pull in additional frameworks or dependencies, add them to this file
- create and customize a `local.py` settings file, e.g., `cp miracle/settings/local.py.example miracle/settings/local.py`
- run `fab setup` to setup and initialize the database - this assumes that you have `trust` permissions set up in your
  `pg_hba.conf` file for local connections and will fail otherwise. Otherwise, create the postgres databases and users
  yourself and then run `fab init_db` to initialize and create the schema.
