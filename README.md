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

La API expone operaciones RESTful estándar sobre el recurso `/items` y un endpoint raíz.

| Método | Endpoint | Descripción | Códigos de Respuesta |
|---|---|---|---|
| `GET` | `/` | Healthcheck y metadatos dinámicos del servicio (`version`, `status`) | `200 OK` |
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
* En runtime, el endpoint `/` resuelve la versión instalada mediante `tomllib` de forma nativa sin acoplamientos estáticos.
* Los mensajes de commit deben respetar la especificación de **Conventional Commits**:
  * `fix:` incrementa el segmento **PATCH** (`0.1.0` -> `0.1.1`).
  * `feat:` incrementa el segmento **MINOR** (`0.1.0` -> `0.2.0`).
  * `feat!:` o `BREAKING CHANGE:` incrementa el segmento **MAJOR** (`0.1.0` -> `1.0.0`).

---

## Pipelines de CI/CD (GitHub Actions)

El ciclo de integración y entrega continua se desacopla en dos flujos independientes según el evento:

   **Integración Continua (`ci.yml`):**
   * Se ejecuta ante cada `pull_request` contra la rama `main`.
   * Realiza un shallow clone completo (`fetch-depth: 0`) para validar que todos los commits introducidos en la rama sigan la convención (`cz check`).
   * Instala las dependencias con caché optimizado de `uv`.
   * Ejecuta la suite de pruebas unitarias con reporte de cobertura obligatorio (`pytest --cov=app --cov-report=term-missing`).


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
   uv run uvicorn app.main:app --reload --port 8000
   ```

3. **Acceder a la documentación interactiva:**
   * Swagger UI: `http://localhost:8000/docs`
   * Redoc: `http://localhost:8000/redoc`

### Opción B: Entorno Contenedorizado con Docker Compose

Para levantar el entorno completo de desarrollo con recarga en caliente sin instalar dependencias en el host:

```bash
docker compose up

# O en segundo plano
docker compose up -d
```

---

## Ejecución de Tests y Cobertura

La suite de pruebas valida contratos HTTP, lógica de persistencia en memoria y manejo de excepciones mediante el cliente asíncrono de Starlette/FastAPI:

```bash
# Ejecución estándar de tests
uv run pytest -v

# Ejecución con reporte de cobertura detallado
uv run pytest -v --cov=app --cov-report=term-missing
```
