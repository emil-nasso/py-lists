import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import deps
from app.field_types import FieldTypeCreateUnion
from app.models import List
from app.schemas import ItemValues, ListCreate, ListUpdate

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = deps.get_list_repository()
    print(f"Loaded {len(repository.get_all())} lists from storage.")
    yield


app = FastAPI(title="List Making API", lifespan=lifespan)


@app.get("/lists", response_model=list[List], tags=["lists"])
def get_lists(list_repository: deps.ListRepository) -> list[List]:
    return list_repository.get_all()


@app.get("/lists/{list_id}", response_model=List, tags=["lists"])
def get_list(list_id: UUID, list_repository: deps.ListRepository) -> List:
    list = list_repository.get(list_id)
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    return list


@app.post("/lists", response_model=List, status_code=201, tags=["lists"])
def create_list(list_create: ListCreate, list_repository: deps.ListRepository) -> List:
    list = List(name=list_create.name)
    return list_repository.add(list)


@app.put("/lists/{list_id}", response_model=List, tags=["lists"])
def update_list(
    list_id: UUID, list_update: ListUpdate, list_repository: deps.ListRepository
) -> List:
    list = list_repository.update(list_id, list_update.name)
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    return list


@app.delete("/lists/{list_id}", status_code=204, tags=["lists"])
def delete_list(list_id: UUID, list_repository: deps.ListRepository) -> None:
    deleted = list_repository.delete(list_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="List not found")


@app.post("/lists/{list_id}/fields", response_model=List, status_code=201, tags=["fields"])
def add_field_to_list(
    list_id: UUID, field_create: FieldTypeCreateUnion, list_repository: deps.ListRepository
) -> List:
    list = list_repository.add_field(list_id, field_create)
    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    return list


@app.delete(
    "/lists/{list_id}/fields/{field_id}", response_model=List, status_code=200, tags=["fields"]
)
def delete_field_from_list(
    list_id: UUID, field_id: UUID, list_repository: deps.ListRepository
) -> List:
    list = list_repository.delete_field(list_id, field_id)
    if not list:
        raise HTTPException(status_code=404, detail="List or field not found")
    return list


@app.post("/lists/{list_id}/items", response_model=List, status_code=201, tags=["items"])
def add_item_to_list(
    list_id: UUID, item_values: ItemValues, list_repository: deps.ListRepository
) -> List:
    try:
        list = list_repository.add_item(list_id, item_values.field_values)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not list:
        raise HTTPException(status_code=404, detail="List not found")
    return list


@app.put("/lists/{list_id}/items/{item_id}", response_model=List, status_code=200, tags=["items"])
def update_item_in_list(
    list_id: UUID, item_id: UUID, item_values: ItemValues, list_repository: deps.ListRepository
) -> List:
    try:
        list = list_repository.update_item(list_id, item_id, item_values.field_values)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not list:
        raise HTTPException(status_code=404, detail="List or item not found")
    return list


@app.delete(
    "/lists/{list_id}/items/{item_id}", response_model=List, status_code=200, tags=["items"]
)
def delete_item_from_list(
    list_id: UUID, item_id: UUID, list_repository: deps.ListRepository
) -> List:
    list = list_repository.delete_item(list_id, item_id)
    if not list:
        raise HTTPException(status_code=404, detail="List or item not found")
    return list


# Mount static files - must be last to avoid catching API routes
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
