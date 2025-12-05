import functools
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from app.field_types import (
    BooleanFieldHandler,
    ImageFieldHandler,
    NumberFieldHandler,
    TextFieldHandler,
    URLFieldHandler,
)
from app.field_types import (
    FieldHandlerRegistry as _FieldHandlerRegistry,
)
from app.migration import DataMigrator as _DataMigrator
from app.persistence import PersistenceManager as _PersistenceManager
from app.repositories import ListRepository as _ListRepository
from app.seeder import ListSeeder as _ListSeeder


# Singletons
@functools.lru_cache
def get_field_registry() -> _FieldHandlerRegistry:
    """Get the singleton field handler registry."""
    registry = _FieldHandlerRegistry()

    # Register all field types
    registry.register(BooleanFieldHandler())
    registry.register(TextFieldHandler())
    registry.register(NumberFieldHandler())
    registry.register(URLFieldHandler())
    registry.register(ImageFieldHandler())

    return registry


@functools.lru_cache
def get_persistence_manager() -> _PersistenceManager:
    """Get the singleton persistence manager."""
    storage_root = Path(__file__).parent.parent / "storage"
    return _PersistenceManager(storage_root=storage_root)


@functools.lru_cache
def get_migrator() -> _DataMigrator:
    """Get the singleton data migrator."""
    return _DataMigrator(persistence_manager=get_persistence_manager())


@functools.lru_cache
def get_list_repository() -> _ListRepository:
    """Get the singleton list repository."""
    return _ListRepository(
        field_registry=get_field_registry(),
        persistence_manager=get_persistence_manager(),
        migrator=get_migrator(),
    )


@functools.lru_cache
def get_list_seeder() -> _ListSeeder:
    return _ListSeeder(repository=get_list_repository())


# Dependency declarations
FieldHandlerRegistry = Annotated[_FieldHandlerRegistry, Depends(get_field_registry)]
PersistenceManager = Annotated[_PersistenceManager, Depends(get_persistence_manager)]
Migrator = Annotated[_DataMigrator, Depends(get_migrator)]
ListRepository = Annotated[_ListRepository, Depends(get_list_repository)]
ListSeeder = Annotated[_ListSeeder, Depends(get_list_seeder)]
