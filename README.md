How to prepare project:
1. `poetry install`
2. `poetry shell`
3. `docker compose build`
4. `make migrate`

To run the project:
1. `make up-bg`
2. `make run-worker`
3. `make run-api`

To run linter:
1. `ruff . --fix`

To add migration:
1. `make add-migration`
