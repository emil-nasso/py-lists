# py-lists

A tiny FastAPI project for building flexible lists. Define lists, attach typed fields (text, number, boolean, URL, image, etc), and add items whose values are validated against those fields. Data is stored on disk under `storage/lists/{list_id}/list.json` so the API boots with whatever you created previously.

## Quick start

Requirements: Python 3.12+ and [uv](https://github.com/astral-sh/uv) installed locally.

```bash
# Install dependencies
uv sync

# Run the dev server (http://localhost:8000, docs at /docs)
uv run fastapi dev app/main.py
```

### Docker

```bash
docker build -t py-lists .
docker run --rm -p 8000:8000 py-lists
```

The interactive OpenAPI docs are available at `/docs` once the server is running.
