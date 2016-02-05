### Setup

* Copy or rename the example files (remove `.example` from file names: `django/miracle/settings/local.py.example` and `docker-compose.yml.example`)
* Change all passwords, keys and secrets
  - `docker-compose.yml`
  - `deployr/addUser.py`
  - `django/entrypoint.sh`
  - `django/miracle/settings/local.py`
  - radiant-mod: `/srv/shiny-server/base/tools/data/manage_ui.R` (this can be changed afterwards)
* Change uid as needed (`docker/min.Dockerfile`)
* Build the images and start containers

```
./build.sh
```

* `miracle` homepage will be live at `http://localhost:9999/

### Setup with Nginx on the host

* Make sure the uid of the Nginx user matches the uid in `docker/min.Dockerfile`
* Create `static` and `socket` folders, owned by the Nginx user, and modify `docker-compose.yml`
    - Change `- /miracle/socket` to `- host_path/socket:/miracle/socket`
    - Change `- /miracle/static` to `- host_path/static:/miracle/static`
    - Remove the nginx section
* Turn off debug mode and debug toolbar
