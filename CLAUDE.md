# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Night Eye API - An AI-powered brand identity and trend analysis platform. The service uses Temporal.io for workflow orchestration and LiteLLM for LLM interactions. It processes fashion brand data to extract brand DNA, classification, and trend analysis.

## Common Commands

```bash
# Install dependencies
make install

# Run the server (default: localhost:8097)
make run
# or directly:
python entrypoint.py

# Database migrations
make migrate      # Create new migration (prompts for message)
make upgrade      # Apply pending migrations

# Clean cache files
make clean
```

### Alembic Migrations

```bash
# Create migration manually
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## Architecture

### Application Structure

- **Entry Point**: `entrypoint.py` -> `app/main.py` -> `app/application.py`
- **Server**: FastAPI with uvicorn + uvloop async event loop
- **Routing**: API versioned under `/v1.0/`, health checks at `/_healthz` and `/_readyz`

### Domain Modules

Each domain (brand, collection, themes, trend) follows the same pattern:
```
<domain>/
  models.py       # SQLAlchemy models (extend Base, EpochTimestampMixin)
  schemas.py      # Pydantic schemas for API
  dao.py          # Data Access Object (extends BaseDAO)
  service.py      # Business logic layer
  views.py        # Request handlers
  routes.py       # FastAPI router definitions
  temporal/
    constants.py  # Queue names (TemporalQueue enum)
    workflow.py   # Temporal workflow definitions (@workflow.defn)
    activities/   # Temporal activities (@activity.defn)
    workers/      # Worker registration (@register_worker decorator)
    temporal_client.py  # Client for starting workflows
```

### Data Layer

- **PostgreSQL**: Primary database via SQLAlchemy async (`asyncpg` driver)
- **MongoDB**: Document store via Beanie + Motor for some models
- **Elasticsearch**: Vector search for fashion/trend data
- **Redis**: Caching layer

### Configuration

Config is loaded from `config/default.yaml` and environment variables via `configargparse`:
- `config/config_parser.py` - Argument parsing
- `config/settings.py` - `Settings` class with `loaded_config` singleton
- Server type controlled by `server_type` config (e.g., "night_eye")

### Temporal Workflows

Workflows orchestrate LLM-powered activities:
1. Workflow starts via `temporal_client.py` starting a workflow execution
2. Worker processes tasks from queue (`@register_worker` decorator in `utils/temporal/worker_registry.py`)
3. Activities call LiteLLM with Pydantic schemas for structured output

**Activity Pattern**:
```python
@activity.defn
async def my_activity(state: Dict[str, Any]) -> Dict[str, Any]:
    # Call LiteLLM with structured output
    response = await litellm.aresponses(
        model=DEFAULT_MODEL,
        input=PROMPT.format(...),
        text_format=MyPydanticSchema,
        reasoning=REASONING_HIGH,
    )
    result = MyPydanticSchema.model_validate_json(response.output_text)
    state["result"] = result.model_dump()
    return state
```

### Connection Management

- `utils/connection_manager.py` - SQLAlchemy session factory
- `utils/connection_handler.py` - Async context manager for sessions
- Use `get_connection_handler_for_app()` context manager for database operations:
```python
async with get_connection_handler_for_app() as connection_handler:
    dao = MyDAO(connection_handler.session)
    result = await dao.my_method()
    await connection_handler.session.commit()
```

### Key Dependencies

- **LiteLLM**: LLM abstraction layer with structured output via Pydantic `text_format`
- **Temporal.io**: Durable workflow execution
- **FastAPI + Pydantic v2**: API framework
- **SQLAlchemy 2.0**: Async ORM with `asyncpg`
- **uuid6**: UUID7 for time-ordered primary keys

## Environment

- Python 3.12
- Default port: 8097
- Temporal: localhost:7233 (default namespace)
- PostgreSQL: localhost:5432/nighteye
- MongoDB: localhost:27017/brand_identity
- Redis: localhost:6379/3
