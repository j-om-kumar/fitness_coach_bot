run:
	uvicorn main:app --reload

db-pull:
	docker compose up -d

db-setup:
	export DATABASE_URL="postgresql+asyncpg://postgres:coachpass@localhost:5432/coachdb" && python ./app/db/db_init.py