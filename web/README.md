# Parser Web

Frontend project on React + TypeScript for Vacancy Radar.

## Features

- Trigger parser job via `parser_api` (`POST /api/v1/parsing/jobs`).
- Browse vacancies from API (`GET /api/v1/vacancies`).
- Filter by search/city/experience.
- Simple pagination.
- Admin-only link to external Streamlit dashboards.

## Environment

- `VITE_API_BASE_URL` - base URL of `parser_api` (default `http://localhost:8000`).
- `VITE_STREAMLIT_DASHBOARD_URL` - URL of external Streamlit dashboard (for admin link).
- `VITE_DASHBOARD_ADMIN_EMAILS` - comma-separated admin emails allowed to see dashboard link.

Example:

```env
VITE_API_BASE_URL=https://api.elertka.tech
VITE_STREAMLIT_DASHBOARD_URL=https://dash.elertka.tech
VITE_DASHBOARD_ADMIN_EMAILS=admin1@elertka.tech,admin2@elertka.tech
```

## Local run

1. `cp .env.example .env`
2. `npm install`
3. `npm run dev -- --host 0.0.0.0 --port 5173`
4. Open `http://localhost:5173`

## Docker run

1. `cp .env.example .env`
2. `docker compose up -d --build`
3. Open `http://localhost:3000`

## Makefile shortcuts

- `make install` - install dependencies.
- `make dev` - run dev server.
- `make build` - create production build.
- `make check` - run eslint.
- `make compose-up` - build and start container.
- `make compose-down` - stop container.
- `make compose-logs` - stream container logs.

## Styling

- SCSS is used for styles.
- Shared tokens: `src/styles/_variables.scss`
- Shared mixins: `src/styles/_mixins.scss`
