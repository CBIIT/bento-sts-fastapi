# bento-sts-fastapi Development Information

This is a rewrite of the [bento-sts](https://github.com/CBIIT/bento-sts) 
following the ticket DATATEAM-268. This lays out the following requirements:

* Remove web interface code and reduce to API only
* Replace Flask with [FastAPI](https://fastapi.tiangolo.com) as the coding framework
* Attempt to refactor so that we can create a drop-in replacement Docker image for 
  deployment (see https://github.com/CBIIT/bento-mdb/tree/main/devops/dockerfiles/sts)


## Getting started

### Set up working environment

To set up a local working environment:

[Get uv](https://docs.astral.sh/uv/#installation) and then run the following

```shell
git clone https://github.com/CBIIT/bento-sts-fastapi
cd bento-sts-fastapi
uv venv
uv pip install -e .
```

### Connect to or set up a running MDB

To configure a Neo4j MDB database that bento-sts will connect with, copy [env.eg](/env.eg)
to a file called `.env`, then edit that file to set the Bolt endpoint, username, and password
of a running database.

The easiest way to get a legit MDB running on your machine is 
to use Docker to run the image [maj1/test-mdb:neo4.4](https://hub.docker.com/layers/maj1/test-mdb/neo4.4/images/sha256-777659d5d2a3dfb7c6828cde37af3e9845d29445656eeeb63a19ae5ae1ea2121)
in a background container:

```shell
docker run -d -p 7474:7474 -p 7687:7687 --name test-mdb maj1/test-mdb:neo4.4
```

The container is running properly if you see it running:

```shell
docker ps
CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS         PORTS                                                                                      NAMES
327f38a22cb6   maj1/test-mdb:neo4.4   "tini -g -- /startup…"   3 minutes ago   Up 3 minutes   0.0.0.0:7474->7474/tcp, [::]:7474->7474/tcp, 0.0.0.0:7687->7687/tcp, [::]:7687->7687/tcp   test-mdb
```

_and_ its logs show Neo4j started successfully:

```shell
docker logs test-mdb
2025-10-08 23:07:25.544+0000 INFO  ======== Neo4j 4.4.25 ========
...
2025-10-08 23:07:29.105+0000 INFO  name: system
2025-10-08 23:07:29.105+0000 INFO  creationDate: 2024-01-31T19:49:28.195Z
2025-10-08 23:07:29.105+0000 INFO  Started.
```

You shouldn't need to change anything in `.env` for bento-sts to connect successfully.

### Start a dev FastAPI server

Now you can start a dev server like so:

```shell
uv run fastapi dev src/bento_sts/sts.py
```

In a browser, go to http://127.0.0.1:8000/docs. If everything is working, you should see 
an interactive Swagger user interface that will list all the endpoints and allow queries.

The dev server will automatically reload as you change the code.

## Code Structure



The API endpoints and associated DB queries are distributed among the files in the 
[routers](/src/bento_sts/routers) directory. 
