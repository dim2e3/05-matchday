.PHONY: up down logs test test-backend test-backend-pg test-frontend lint e2e demo-live demo-final demo-drift demo-reset

COMPOSE := docker compose
FAKE := http://127.0.0.1:8090

up:
	$(COMPOSE) up --build -d --wait

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api worker

test: test-backend test-frontend

test-backend:
	uv --directory backend run pytest -q

# Same suite against a throwaway Postgres (what CI does).
PG_TEST := postgresql+asyncpg://matchday:matchday@127.0.0.1:55432/matchday_test
test-backend-pg:
	docker run -d --rm --name md-pg-test -e POSTGRES_USER=matchday -e POSTGRES_PASSWORD=matchday \
	  -e POSTGRES_DB=matchday_test -p 127.0.0.1:55432:5432 postgres:16-alpine >/dev/null
	until docker exec md-pg-test pg_isready -U matchday -q; do sleep 1; done
	TEST_DATABASE_URL=$(PG_TEST) uv --directory backend run pytest -q; \
	  status=$$?; docker rm -f md-pg-test >/dev/null; exit $$status

test-frontend:
	npm --prefix frontend test

lint:
	uv --directory backend run ruff check .
	npm --prefix frontend run lint

e2e:
	npm --prefix e2e test

# Drive fake-espn by hand (game 401886427 = DAL @ STL, NHL).
demo-live:
	curl -s -XPOST $(FAKE)/_control/game -H 'content-type: application/json' \
	  -d '{"game_id":"401886427","state":"in","home_score":1,"away_score":0}'

demo-final:
	curl -s -XPOST $(FAKE)/_control/game -H 'content-type: application/json' \
	  -d '{"game_id":"401886427","state":"post","home_score":3,"away_score":2}'

demo-drift:
	curl -s -XPOST $(FAKE)/_control/drift -H 'content-type: application/json' \
	  -d '{"mode":"renamed_competitors"}'

demo-reset:
	curl -s -XPOST $(FAKE)/_control/reset
