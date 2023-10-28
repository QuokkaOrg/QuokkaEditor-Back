up-bg:
	docker compose up -d db redis rabbitmq

run-api:
	docker compose run --rm --service-ports --no-deps api

run-worker:
	docker compose run --rm --service-ports --no-deps worker

migrate:
	docker compose run --rm --service-ports --no-deps api aerich upgrade

add-migration:
	docker compose run --rm --service-ports --no-deps api aerich migrate