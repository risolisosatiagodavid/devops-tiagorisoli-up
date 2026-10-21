# Inventory Management API

API REST construida con FastAPI para la gestión de inventario, desarrollada en el marco del Trabajo Práctico de la materia DevOps.

El objetivo central del proyecto es servir como caso de estudio práctico para implementar un ciclo de vida de desarrollo de software moderno y seguro (SDLC): arquitectura de empaquetado multi-stage, aislamiento reproducible de entornos con `uv`, automatización de pruebas unitarias y cobertura, versionado semántico formal y pipelines de CI/CD con GitHub Actions.

---

## Stack Tecnológico

* **Lenguaje y Framework:** Python 3.11+, FastAPI, Pydantic v2.
* **Gestor de Entorno y Paquetes:** `uv` (resolución determinística basada en `uv.lock`).
* **Testing & Calidad:** `pytest`, `pytest-cov`, `httpx`.
* **Versionado y Changelog:** Commitizen (`cz_conventional_commits`, SemVer 2.0).
* **Contenedores:** Docker, Docker Compose, Multi-stage builds, Google Distroless.
* **CI/CD:** GitHub Actions (Validación de PRs y Releases automatizados).

---

## Decisiones de Arquitectura: Docker Multi-Stage y Google Distroless

La imagen de contenedor se organiza en un `Dockerfile` multi-stage con dos targets específicos para desacoplar el entorno de desarrollo del de producción:

### Target `dev`
* Utiliza una imagen base de Python completa (`python:3.11-slim`).
* Incluye herramientas de testing, depuración y utilidades de shell.
* Soporta hot-reload (`--reload`) sincronizado con el host mediante bind mounts en `compose.yaml` (`./app:/app/app` y `./pyproject.toml:/app/pyproject.toml:ro`).

### Target `prod` y Justificación de Google Distroless
Para la imagen final de despliegue se utiliza `gcr.io/distroless/python3-debian12`:

1. **Reducción radical de la superficie de ataque:** Las imágenes Distroless contienen estrictamente el runtime de Python y sus librerías compartidas mínimas. No incluyen shell (`/bin/sh`, `/bin/bash`), administradores de paquetes (`apt`, `dpkg`) ni binarios estándar del sistema operativo (`curl`, `wget`, `nc`).
2. **Mitigación de RCE (Remote Code Execution):** En caso de una vulnerabilidad de ejecución remota de código en la aplicación o sus dependencias, un atacante no puede invocar shells secundarios, ejecutar scripts maliciosos ni descargar binarios de post-explotación.
3. **Escaneo de Vulnerabilidades (CVEs):** Al eliminar paquetes y utilidades accesorias del sistema operativo base, se reduce drásticamente el ruido de falsos positivos y la presencia de vulnerabilidades críticas o altas en análisis estáticos de contenedores (Trivy, Grype).
4. **Principio de Mínimo Privilegio e Inmutabilidad:** La aplicación se ejecuta bajo un usuario sin privilegios (`nonroot`)

---

## Endpoints de la API

La aplicación sirve el panel web en `/` y expone operaciones RESTful estándar sobre el recurso `/items`.

| Método | Endpoint | Descripción | Códigos de Respuesta |
|---|---|---|---|
| `GET` | `/` | Panel web de gestión del inventario | `200 OK` |
| `GET` | `/health` | Página visual con el estado del servicio | `200 OK` |
| `GET` | `/healthz` | Healthcheck JSON para monitoreo y automatizaciones | `200 OK` |
| `GET` | `/items` | Lista la totalidad del inventario registrado | `200 OK` |
| `GET` | `/items/{item_id}` | Obtiene el detalle de un ítem por ID | `200 OK`, `404 Not Found` |
| `POST` | `/items` | Crea un nuevo ítem en el inventario | `201 Created` |
| `PATCH` | `/items/{item_id}` | Actualización parcial de campos de un ítem | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/items/{item_id}` | Remueve un ítem del inventario de forma idempotente | `204 No Content`, `404 Not Found` |

### Esquema de Datos (`Item`)

```json
{
  "name": "string",
  "price": 0.0,
  "quantity": 0.0
}
```

---

## Versionado Semántico y Conventional Commits

El proyecto implementa **Semantic Versioning (SemVer)** automatizado mediante **Commitizen**. 

* La versión oficial del proyecto se gestiona como fuente única de verdad en la clave `project.version` de `pyproject.toml`.
* En runtime, el endpoint `/healthz` resuelve la versión instalada mediante `tomllib` de forma nativa sin acoplamientos estáticos.
* Los mensajes de commit deben respetar la especificación de **Conventional Commits**:
  * `fix:` incrementa el segmento **PATCH** (`0.1.0` -> `0.1.1`).
  * `feat:` incrementa el segmento **MINOR** (`0.1.0` -> `0.2.0`).
  * `feat!:` o `BREAKING CHANGE:` incrementa el segmento **MAJOR** (`0.1.0` -> `1.0.0`).
  * `docs:`, `ci:` y `test:` no incrementan la versión de la API por sí solos.

  Al integrar cambios en `main`, el workflow de CD publica `docker.io/<usuario>/inventoryapi-api:<project.version>` y solicita a Render desplegar esa imagen. La versión del tag Docker se lee de `pyproject.toml`; si se integran varios cambios sin incrementar la versión, el mismo tag se vuelve a publicar y Render despliega su contenido actualizado. Por eso, incrementa la versión en `pyproject.toml` cuando corresponda según Conventional Commits. `prod` y `latest` no se usan como referencias de despliegue.

---

## Pipelines de CI/CD (GitHub Actions)

El ciclo de integración y entrega continua se desacopla en dos flujos independientes según el evento:

   **Integración Continua (`ci.yml`):**
   * Se ejecuta ante cada `pull_request` contra la rama `main`.
   * Descarga el historial completo para validar los commits del PR (`cz check`).
   * Ejecuta la suite con cobertura, levanta la API mediante Compose y corre k6 con umbrales de latencia y errores.

   **Entrega Continua (`cd.yml`):**
   * Se ejecuta al hacer push a `main` (por ejemplo, al integrar un PR), corre los tests y publica la imagen usando `project.version`.
   * Invoca el Deploy Hook de Render pasando la misma etiqueta de imagen publicada.


---

## Prerrequisitos

* Python 3.11+
* [`uv`](https://github.com/astral-sh/uv) (gestor de paquetes y entornos virtuales)
* Docker y Docker Compose v2+

---

## Ejecución Local

### Opción A: Entorno Nativo con `uv`

1. **Instalar dependencias (incluyendo herramientas de desarrollo y tests):**
   ```bash
   uv sync --all-extras --dev
   ```

2. **Iniciar el servidor con hot-reload:**
   ```bash
   uv run uvicorn app.main:app --reload --port 8000 --no-access-log --log-config app/core/logging_config.json
   ```

3. **Acceder a la documentación interactiva:**
   * Panel web: `http://localhost:8000/`
   * Estado del servicio: `http://localhost:8000/health`
   * Swagger UI: `http://localhost:8000/docs`
   * Redoc: `http://localhost:8000/redoc`

   Si modificas productos desde Swagger mientras el panel está abierto, usa el botón **Actualizar** del listado o volve a la pestaña del panel para cargar los cambios.

### Opción B: Entorno Contenedorizado con Docker Compose

Para levantar el entorno completo de desarrollo con recarga en caliente sin instalar dependencias en el host:

```bash
docker compose up

# O en segundo plano
docker compose up -d
```

El entorno local inicia Grafana, Prometheus, Tempo y OpenTelemetry Collector. Esta configuración usa Grafana autogestionado localmente (no Grafana Cloud): Prometheus recolecta las métricas HTTP desde `/metrics` y la API exporta trazas por OTLP al Collector, que las envía a Tempo. Puedes comprobar Prometheus en `http://localhost:9090`. Abre Grafana en `http://localhost:3000` (usuario y contraseña iniciales: `admin` / `admin`; puedes definir `GRAFANA_ADMIN_PASSWORD` para cambiarla).

El dashboard **Inventory API - RED** fue diseñado para este proyecto y se aprovisiona desde [inventory-api.json](./observability/grafana/dashboards/inventory-api.json); no parte de una plantilla. Muestra tráfico en requests por minuto (RPM), latencia p50 y p95 por ruta y la tasa de errores HTTP 4xx/5xx, además del porcentaje de respuestas 2xx y la latencia promedio. En **Explore**, selecciona **Tempo** para inspeccionar trazas. Genera tráfico abriendo `http://localhost:8000/` o consultando `/items`; puedes generar un 404 consultando `/items/999999`.

#### Generar tráfico de carga con k6

Con el stack local iniciado, ejecuta la prueba acotada con:

```bash
docker compose --profile load-test run --rm k6
```

k6 consulta `/items` y genera un 404 esperado en una de cada cinco iteraciones para alimentar también las métricas de error. El escenario dura unos 50 segundos con hasta 3 usuarios virtuales, valida los códigos HTTP y exige p95 menor a 500 ms. Los errores 404 son parte intencional del tráfico y se consideran respuestas esperadas para k6. Mientras corre, abre **Inventory API - RED** en Grafana y selecciona una ventana que incluya el test (por ejemplo, **Last 5 minutes**). Para apuntar a otra URL, se define `K6_BASE_URL`; por defecto, dentro de Compose apunta a `http://api:8000`.

El workflow de CI también levanta la API con `docker compose up --build --wait --wait-timeout 90 api`; Compose usa el healthcheck de `/healthz` para esperar a que esté lista y después corre el mismo escenario de k6 en cada pull request hacia `main`. Si k6 falla sus checks o umbrales, el job de CI falla; al finalizar, el workflow elimina sus contenedores y volúmenes efímeros.

La API emite un log JSON por request con `timestamp`, `level`, `path` y `status_code` (además de método, duración, `trace_id` y `span_id`). En rutas instrumentadas, esos identificadores corresponden al span HTTP de OpenTelemetry: copia el `trace_id` del log y búscalo en **Grafana > Explore > Tempo** para abrir la traza relacionada. Las rutas excluidas de tracing, como health checks y `/metrics`, pueden tener los identificadores en `null`. Los logs se escriben en stdout del contenedor; todavía no se envían a Grafana como un datasource de logs. El access log de Uvicorn está desactivado para evitar líneas duplicadas sin estructura. Los endpoints `/metrics`, `/healthz`, `/health` y los recursos estáticos quedan excluidos de las métricas de requests, pero los logs de requests se conservan. Las métricas usan rutas parametrizadas para evitar etiquetas de alta cardinalidad, por ejemplo `/items/{item_id}`. El histograma permite calcular percentiles por ruta; p50 y p95 representan la distribución de latencia de las requests en la ventana elegida. La instrumentación SQLAlchemy requiere SQLAlchemy 2.0.x; la dependencia está acotada a esa versión para que OpenTelemetry también produzca spans de base de datos.

Para levantar el entorno de produccion:

```bash
docker compose -f compose.prod.yaml up
```

---

## Ejecución de Tests y Cobertura

La suite de pruebas valida contratos HTTP, persistencia SQLite y manejo de excepciones mediante el cliente de Starlette/FastAPI:

```bash
# Ejecución estándar de tests
uv run pytest -v

# Ejecución con reporte de cobertura detallado
uv run pytest -v --cov=app --cov-report=term-missing
```

La aplicación acepta `DATABASE_URL` para configurar SQLite. Si no se define, usa `inventory.db` en la raíz del proyecto; Docker Compose configura `/data/inventory.db` en su volumen persistente y CI usa una base temporal aislada.
