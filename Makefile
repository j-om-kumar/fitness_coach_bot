run:
	uvicorn main:app --reload

fly-setup:
	brew install flyctl

launch:
	fly launch --no-deploy --name fitness-coach

deploy:
	fly deploy

db-pull:
	docker compose -f postgres-docker-compose.yaml up -d

db-setup:
	export DATABASE_URL="postgresql+asyncpg://postgres:coachpass@localhost:5432/coachdb" && python ./app/db/db_init.py


db-push:
	fly db push