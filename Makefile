.PHONY: up down logs test test-backend test-frontend lint e2e demo-live demo-final demo-drift demo-reset

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
