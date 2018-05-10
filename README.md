# Docker Flask Template

A dockerized template for a flask application written in Python 3.6.

> Before you continue install [Docker](https://docs.docker.com/install/).

# Installation

Run the following command to clone this repository, `cd` into it, and build the Docker images.

```bash
git clone https://github.com/rmorshea/docker-flask-template.git && \
cd docker-flask-template && \
docker-compose build
```

# Run The Application

Set up your environment variables (be sure to change these later):

```bash
# whether or not to run the application in debug mode.
export FLASK_DEBUG=1
# the password for the postgresql user "docker".
export POSTGRES_PASSWORD=secret
# a secret used to cryptographically sign access tokens.
export JWT_SECRET_KEY=secret
# the password of the application's "root" user.
export ROOT_USER_PASSWORD=secret
```

Run the application:

```bash
docker-compose up
```

# Available Endpoints

Once the application is running see [localhost:80/apidocs](http://localhost:80/apidocs) for api details.

# Bootstrap Users And Groups

When you first run the application only one user exists. This user, with root privileges, must bootstrap all other users and groups into the system. To begin this process we must get an access token for the `root` user and store it (you'll need the `ROOT_USER_PASSWORD` environment variable to run this):

```bash
ACCESS_TOKEN=`curl -X POST \
-H "Content-Type: application/json" \
-d '{"username":"root", "password":"'"$ROOT_USER_PASSWORD"'"}' \
http://localhost:80/user/login`
```

The `root` user, and sole member of the `root` group, can create and manage other groups. Users cannot create groups whose `level` is equal or higher than their own. The `root` group has a level of `0`. Thus the root user can only make groups whose levels are `1` or greater:

```bash
curl -X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-d '{"name":"admin", "manager":"root", "level":1}' \
http://localhost:80/group/create
```

The root user, as a manager of this new `admin` group can add new users to it:

```bash
curl -X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $ACCESS_TOKEN" \
-d '{"username":"admin", "password":"secret", "groups":["admin"]}' \
http://localhost:80/user/create
```
