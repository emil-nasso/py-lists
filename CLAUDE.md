# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A FastAPI-based list-making API that allows users to create customizable lists with dynamic field types. Lists support various field types (text, number, boolean, URL) and persist data to disk as JSON files.

## Development Commands

### Setup and Running
```bash
# Install dependencies
make sync

# Run development server (with hot reload)
make run
# Runs: uv run fastapi dev app/main.py
# Server available at http://localhost:8000
```

### Code Quality
```bash
# Run linter with auto-fix
make lint

# Format code
make format

# Type check with pyright
make type-check

# Run both lint and type-check
make check
```

### Docker
```bash
# Build Docker image
make docker-build

# Run in Docker container
make docker-run
# Exposes port 8000
```

## Architecture

### Core Design Pattern: Handler Registry System

The application uses a handler registry pattern for extensible field type management. This is the most important architectural decision in the codebase.

**Key files:**
- `app/field_types.py` - Complete field type system (529 lines)
- `app/repositories.py` - Business logic layer
- `app/persistence.py` - Disk persistence layer
- `app/deps.py` - Dependency injection using lru_cache singletons

### Data Flow

1. **Request** → FastAPI endpoint in `app/main.py`
2. **Dependency Injection** → `deps.py` provides singleton instances
3. **Repository Layer** → `repositories.py` handles business logic
4. **Field Registry** → `field_types.py` validates and processes field operations
5. **Persistence** → `persistence.py` writes to `storage/lists/{list-id}/list.json`

### Field Type System

All field types follow a handler pattern defined in `app/field_types.py`:

- **Handler Base Class**: `FieldHandler[TFieldType, TFieldTypeCreate]` - abstract base with generic types
- **Concrete Handlers**:
  - `BooleanFieldHandler` - default: `False`
  - `TextFieldHandler` - default: `""`, supports `multiline` attribute
  - `NumberFieldHandler` - default: `0` (or `min_value` if set)
  - `URLFieldHandler` - default: `""`, validates http/https format
- **Registry**: `FieldHandlerRegistry` - central dispatcher for all field operations

**To add a new field type:**
1. Create model class inheriting from `FieldType` in `field_types.py`
2. Create creation schema inheriting from `FieldTypeCreate`
3. Add both to discriminated unions (`FieldTypeUnion`, `FieldTypeCreateUnion`)
4. Implement handler class inheriting from `FieldHandler`
5. Register handler in `app/deps.py:get_field_registry()`

### Persistence Strategy

Lists are stored as individual JSON files:
```
storage/lists/{uuid}/list.json
```

- **Atomic writes**: Uses temporary file + rename for write safety
- **Load on startup**: All lists loaded into memory via `PersistenceManager.load_all()`
- **Write-through cache**: Every mutation triggers immediate disk write
- **Error handling**: Corrupted files are logged and skipped during load

### Models Structure

- **List**: Container with `fields: dict[UUID, FieldTypeUnion]` and `items: dict[UUID, list[FieldValue]]`
- **FieldValue**: Links a field_id to a value for a specific item
- **Item representation**: Each item is a list of FieldValue objects, keyed by item UUID in the items dict

Example: A list with 2 fields and 3 items has 6 FieldValue instances total (2 fields × 3 items).

## Configuration

### Linting and Type Checking

**Ruff** (pyproject.toml:23-28):
- Line length: 100
- Target: Python 3.12
- Rules: E (errors), F (pyflakes), I (isort), N (naming), W (warnings)

**Pyright** (pyproject.toml:30-32):
- Python version: 3.12
- Mode: strict

### Docker Configuration

Multi-stage build optimized for memory efficiency:
- Single worker with `--limit-concurrency 50`
- Total memory ~80-120MB
- Uses `uv` for dependency management
- Virtual environment in `/app/.venv`

## API Structure

All endpoints in `app/main.py`:

**Lists:**
- `GET /lists` - List all
- `GET /lists/{list_id}` - Get one
- `POST /lists` - Create (requires: `name`)
- `PUT /lists/{list_id}` - Update (requires: `name`)
- `DELETE /lists/{list_id}` - Delete

**Fields:**
- `POST /lists/{list_id}/fields` - Add field (body: discriminated union by `type`)
- `DELETE /lists/{list_id}/fields/{field_id}` - Remove field

**Items:**
- `POST /lists/{list_id}/items` - Add item (body: `field_values` dict)
- `PUT /lists/{list_id}/items/{item_id}` - Update item
- `DELETE /lists/{list_id}/items/{item_id}` - Remove item

**Static files:** Mounted at `/` via `app/static/` directory

## Dependency Injection

Uses FastAPI's dependency system with `functools.lru_cache` for singletons (app/deps.py):

```python
# Internal singletons (lru_cache ensures single instance)
get_field_registry() -> _FieldHandlerRegistry
get_persistence_manager() -> _PersistenceManager
get_list_repository() -> _ListRepository

# Type aliases for FastAPI injection
ListRepository = Annotated[_ListRepository, Depends(get_list_repository)]
```

Always use the annotated types (e.g., `ListRepository`) as function parameters for automatic injection.

## Key Implementation Notes

1. **Field validation**: Delegated to handlers via registry pattern - see `ListRepository._validate_field_values()` in repositories.py:89
2. **Adding fields to existing lists**: Automatically adds default values to all existing items (repositories.py:67-68)
3. **Deleting fields**: Removes field values from all items using list comprehension (repositories.py:84)
4. **Static files must be mounted last**: Comment at main.py:127 - prevents catching API routes
