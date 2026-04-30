# Database Setup Notes

## Stack
- PostgreSQL 16 + PostGIS 3.4 (via `postgis/postgis:16-3.4` Docker image)
- Driver: `psycopg2-binary`
- Migrations: Alembic (autogenerate)

## Local Dev Setup

1. Start the DB container:
   ```
   docker compose up -d
   ```

2. Run migrations:
   ```
   alembic upgrade head
   ```

3. To reset the DB:
   ```
   docker compose down -v
   docker compose up -d
   alembic upgrade head
   ```

## Environment Variables

```
DB_USER=postgres
DB_PASSWORD=<your password>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alert_db
```

## TODOs (before prod)

- **App should not connect as `postgres`.** Create a dedicated DB user (e.g. `aquaalert_app`) with privileges scoped to `alert_db` only. Principle of least privilege. Update `docker-compose.yml` to provision this user at init.
- **Restrict DB to app network in prod.** The DB should not be publicly reachable. App user should be host-restricted.
- **PostGIS filter in `alembic/env.py`.** Current `include_object` filter does not fully exclude PostGIS system tables from autogenerate diffs. Initial migration was trimmed manually. Investigate `include_schemas` or schema-filtering before Phase 3 adds `GEOGRAPHY` columns.
