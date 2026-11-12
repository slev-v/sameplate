# SamePlate

A real-time collaborative meal selection app that helps couples and friends effortlessly agree on what to cook based on shared tastes and available ingredients.

## Tech stack

Python 3.15 · FastAPI · PostgreSQL · SQLAlchemy · Alembic · uv · Docker Compose

## Getting started

Requires Docker with Compose and Make. Run commands from the repository root.

```sh
cp .env.example .env
```

Set your PostgreSQL credentials and database name in `.env`, then run:

```sh
make up
make migrate
```

API documentation: [localhost:8000/docs](http://localhost:8000/docs).

Optionally, load sample recipes into an empty catalog:

```sh
make seed
```

## Development

| Command | Description |
| --- | --- |
| `make logs` | Follow backend logs |
| `make revision MESSAGE="description"` | Generate a database migration |
| `make migrate` | Apply database migrations |
| `make test` | Run tests with a separate PostgreSQL database |
| `make check` | Run lint, formatting checks and tests |
| `make format` | Format Python code |
| `make test-stop` | Stop the temporary test database |
| `make down` | Stop the environment and keep development data |

Run `make help` for all commands.
