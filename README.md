Installation Instructions
=========================

`test_analyses` Requirements
----------------------------

`test_analyses` should contain sample analyses and match the layout in the LUXE
example.

Software Requirements
---------------------

- docker
- docker-compose
- boot2docker (Windows and Mac OSX)

If you want to run on a virtual machine only vagrant is required.

Permission Requirements
-----------------------

In order for the volumes bound to the containers to be writable we need to have
the UID on the docker container to match the UID on the host machine. The 
default UID value for the `django`, `radiant` and `deployr` containers is 1000.
The UID value can be changed by adding `user_id` environment variables to the
`docker-compose.yml` file.

#### Alternative Approach

Instead of matching UIDs with the host and containers data only containers
could be used. These still may require UID matching if the container operating
systems are different because the operating system starts the UIDs at different
places (usually 500 or 1000).

Prepare the Images
------------------

In this directory

```bash
./build-images.sh
```

Prepare the Containers
----------------------

Create the other containers and run them

```bash
sudo docker-compose up
```

Apply migrations

```bash
# assuming django container is called miracle_django_1
sudo docker exec -it miracle_django_1 python manage.py migrate
```

Running the Containers
----------------------

Run the containers after they have been created.

```bash
./start-containers.sh
```

`sudo docker-compose start` does not work because Django dies on start up
if there is no database connectivity (so a 20s sleep is added).

Use `sudo docker-compose stop` to stop the containers and 
`sudo docker-compose rm` to remove stopped containers.

See the `docker-compose` documentation for more information
