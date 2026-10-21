## v0.9.0 (2026-10-21)

### Feat

- add k6 for load testing and traffic generation
- **monitoring**: add logs with json logging integration
- add prometheus integration for monitoring

### Fix

- **telemetry**: correct header format for grafana cloud otel exporting (#33)

## v0.8.0 (2026-10-21)

### Feat

- add k6 for load testing and traffic generation
- **monitoring**: add logs with json logging integration
- add prometheus integration for monitoring

### Fix

- **telemetry**: correct header format for grafana cloud otel exporting (#33)
- attempt to fix render deploy hook issue (#30)
- change render deploy command format (#28)

## v0.7.0 (2026-10-16)

### Feat

- **ui**: add inventory and health dashboards with tests

### Fix

- **compose**: repair db volume permissions causing container to not start
- **Dockerfile**: add missing destination for COPY (pyproject.toml) to resolve buildx parse error (#27)

## v0.6.0 (2026-10-14)

### Feat

- add otel support for future integration

### Refactor

- optimize otel implementation and integration

## v0.5.1 (2026-10-09)

### Fix

- **database**: resolve database relative path issue

## v0.5.1 (2026-10-09)

### Fix

- **database**: resolve database relative path issue

## v0.5.0 (2026-10-02)

### Feat

- add sqlite database session logic

### Fix

- **test_api**: solve clean repository feature db integration

### Refactor

- swap in memory data for database persistence
- add database connection to main.py
- add item model to database.py

## v0.4.0 (2026-09-19)

### Feat

- add patch method and tests (#13)

## v0.3.1 (2026-09-15)

### Feat

- add CI pipeline configuration in ci.yml (#9)

### Fix

- missing version field in read root test

## v0.3.0 (2026-09-15)

### Feat

- add compose for production and development

## v0.2.0 (2026-09-15)

### Feat

- add app version (#6)
- add dockerfile and dockerignore (#4)
- Add unit tests for POST, GET, DELETE (#2)
- scaffold initial FastAPI app and inventory endpoints

### Fix

- resolve error in versioning import format (#7)
- resolve empty dockerignore (#5)
- resolve delete functions returning 422 failing tests
