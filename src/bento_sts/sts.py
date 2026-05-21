import semver
from fastapi import Depends, FastAPI, APIRouter
from importlib.metadata import version as pkg_version
from .dependencies import get_mdb
from .routers import admin, id, model, models, tag, tags, terms

app = FastAPI(
    title="Simple Terminology Server",
    description="""
The Simple Terminology Server (STS) exposes elements of data models in
an intuitive, consistent way. Data models expressed in the form of a
[property graph](https://en.wikipedia.org/wiki/Graph_database#Labeled-property_graph)
-- i.e., as nodes, relationships, properties, and terms -- can be explored and
queried via this interface. Data models are stored in an instance of a
[Metamodel Database (MDB)](https://github.com/CBIIT/bento-meta) backed by a
[Neo4j](https://neo4j.com) server.""",
    version=pkg_version("bento-sts"),
    dependencies=[Depends(get_mdb)]
)

VERSION_PREFIX = "/v" + str(semver.Version.parse(pkg_version("bento-sts")).major)

vrouter = APIRouter(
    prefix=VERSION_PREFIX
)


def _ready_payload() -> dict[str, str]:
    return {
        "application": "STS",
        "version": pkg_version("bento-sts"),
        "status": "READY",
    }


@vrouter.get("")
@vrouter.get("/")
def version_root():
    return _ready_payload()


vrouter.include_router(id.router)
vrouter.include_router(model.router)
vrouter.include_router(models.router)
vrouter.include_router(tag.router)
vrouter.include_router(tags.router)
vrouter.include_router(terms.router)
vrouter.include_router(admin.router)

app.include_router(vrouter)


@app.get("/")
def root():
    return _ready_payload()
