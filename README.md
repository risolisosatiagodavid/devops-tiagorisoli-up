# Inventory Management API

API REST construida con FastAPI para la gestión de inventario, desarrollada en el marco del Trabajo Práctico de la materia DevOps.

El objetivo principal de este proyecto no es únicamente implementar la lógica de negocio, sino servir como caso de estudio práctico para aplicar el ciclo de vida de desarrollo moderno: contenerización eficiente mediante builds multi-stage, aislamiento de entornos, automatización de pruebas unitarias y despliegue continuo mediante pipelines de CI/CD.

---

## Características Principales

- **Framework:** FastAPI con validación estricta de esquemas mediante Pydantic.
- **Gestor de paquetes:** `uv` para resolución determinística y rápida de dependencias.
- **Observabilidad básica:** Middleware asíncrono para medición de latencia interna (`X-Process-Time`).
- **Arquitectura de empaquetado:** Multi-stage Dockerfile con base mínima Distroless para producción y soporte de hot-reload para desarrollo.

---

## Endpoints de la API

La API expone operaciones RESTful estándar sobre el recurso `/items` y un endpoint de verificación de salud del servicio.

| Método | Endpoint | Descripción | Códigos de Respuesta |
|---|---|---|---|
| `GET` | `/` | Healthcheck del servicio | `200 OK` |
| `GET` | `/items` | Obtiene el listado completo de items | `200 OK` |
| `GET` | `/items/{item_id}` | Obtiene el detalle de un item por ID | `200 OK`, `404 Not Found` |
| `POST` | `/items` | Registra un nuevo item en el inventario | `201 Created` |
| `PATCH` | `/items/{item_id}` | Modifica parcialmente campos de un item | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/items/{item_id}` | Elimina un item del inventario | `204 No Content`, `404 Not Found` |

### Esquema de Datos (`Item`)

```json
{
  "name": "string",
  "price": 0.0
}
```
## Prerequisitos
- Python 3.11+
- uv

## Ejecucion
- 1: Instalar dependencias del proyecto
```bash
uv sync
```
- 2: Ejecutar el servidor
```bash
uv run uvicorn app.main:app --reload --port 8000
```

- 3: Documentación interactiva Swagger UI disponible en: http://localhost:8000/docs
