### Setup

* Copy or rename the example files (remove `.example` from file names: `django/miracle/settings/local.py.example` and `docker-compose.yml.example`)
* Change all passwords, keys and secrets
  - `deployr/addUser.py`
  - `django/miracle/settings/local.py`
* Change uid as needed (`docker/min.Dockerfile`)
* Build the images and start containers

```
./build.sh
```

* `miracle` homepage will be live at `http://localhost:9999/

