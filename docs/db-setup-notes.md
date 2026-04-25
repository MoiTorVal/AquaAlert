# Database Setup — Senior-Review TODOs

Improvements to apply before this codebase goes anywhere near prod. Captured after debugging a MySQL auth issue in local dev (a stray `root@172.18.0.1` account with a mismatched password was shadowing `root@%`).

## TODOs

- **App should not connect as `root`.** Create a dedicated MySQL user (e.g. `irrigation_app`) with privileges scoped to `irrigation_db` only. Principle of least privilege. Update `docker-compose.yml` to provision this user at init, and update `.env` (`DB_USER`, `DB_PASSWORD`) accordingly.

- **`root@%` is acceptable in local dev only.** It must not exist in any prod-shaped environment (staging, prod, prod-like CI). In those environments, the database should be reachable only from the application's network, and the app user should be host-restricted.

- **Document the dev MySQL setup in-repo** so the next developer doesn't hit the same wall. Either add a section to the README covering Docker Compose startup + how to reset the local DB, or expand comments in `docker-compose.yml`. Mention the `root@<host-ip>` shadowing pitfall explicitly.
