.PHONY: setup_env up down log db clean_db test deps

PROJECT_NAME=instance_manager


setup_env:
	pip3 install virtualenv
	virtualenv .venv

deps:
	pip3 install -r requirements.txt
	pip3 install -r requirements-dev.txt

up:
	docker compose --profile development up -d --build

down:
	docker compose --profile development down

log:
	docker compose --profile development logs

db:
	docker run -p5432:5432 --name=dev_$(PROJECT_NAME)_db -d -e POSTGRES_USER=dev_user -e POSTGRES_PASSWORD=secret -e POSTGRES_DATABASE=dev_$(PROJECT_NAME) postgres:13

clean_db:
	docker stop dev_$(PROJECT_NAME)_db
	docker rm dev_$(PROJECT_NAME)_db
test:
	cd ./src && PYTHONPATH=./ pytest  --disable-warnings