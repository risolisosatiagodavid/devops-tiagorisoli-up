# Integración con Datadog Cloud (OTLP directo / agentless)

Este directorio centraliza toda la configuración específica de **Datadog Cloud** para producción y desarrollo, manteniendo `app/core/telemetry.py`, `compose.prod.yaml` y `compose.yaml` agnósticos al vendor (OpenTelemetry estándar).

## Contenido

* `compose.datadog.yaml`: override de Docker Compose que conecta la API directamente a la ingesta OTLP de Datadog (`https://otlp.<DD_SITE>`) para **trazas**, **métricas HTTP RED (delta)** y **logs correlacionados**.
* `.env.example`: plantilla de credenciales y sitio de Datadog (`DD_API_KEY`, `DD_SITE`, `DD_SERVICE`, `DD_ENV=production`).
* `dashboard.json`: dashboard **Inventory API - RED** (por defecto en `env:production`) listo para importar en Datadog Cloud.
* `monitors.json`: alertas de producción (`env:production`) para latencia p95 > 500 ms y errores HTTP 5xx.

---

## 1. Producción en Render (despliegue principal)

En el servicio de **Render > Environment**, agrega las siguientes variables estándar de OpenTelemetry:

| Variable | Valor |
|---|---|
| `OTEL_SERVICE_NAME` | `inventory-api` |
| `ENVIRONMENT` | `production` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `https://otlp.<tu-sitio-datadog>` (ej. `https://otlp.datadoghq.com`) |
| `OTEL_EXPORTER_OTLP_HEADERS` | `dd-api-key=<TU_DD_API_KEY>` |
| `OTEL_EXPORTER_OTLP_TRACES_HEADERS` | `dd-api-key=<TU_DD_API_KEY>,compute_stats=true` |
| `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` | `delta` |

Al redeployar (o tras un push a `main` por CD), la imagen `production` (Distroless) comienza a enviar trazas, métricas y logs directamente a Datadog Cloud sin necesidad de sidecar ni Datadog Agent.

---

## 2. Producción con Docker Compose (`compose.prod.yaml`)

1. Copia la plantilla y completa tu API Key y sitio de Datadog:
   ```bash
   cp observability/datadog/.env.example observability/datadog/.env
   ```
2. Levanta el stack de producción conectado a Datadog Cloud:
   ```bash
   docker compose --env-file observability/datadog/.env -f compose.prod.yaml -f observability/datadog/compose.datadog.yaml up -d --build
   ```

---

## 3. Desarrollo local (opcional)

Para probar contra Datadog desde un entorno de desarrollo sin mezclar datos con producción, pasa `DD_ENV=development`:

```bash
DD_ENV=development docker compose --env-file observability/datadog/.env -f compose.yaml -f observability/datadog/compose.datadog.yaml up
```

Y para generar tráfico de prueba con k6:

```bash
DD_ENV=development docker compose --env-file observability/datadog/.env -f compose.yaml -f observability/datadog/compose.datadog.yaml --profile load-test run --rm k6
```

---

## 4. Importar Dashboard y Monitores en Datadog Cloud

* **Dashboard:** en Datadog Cloud **Dashboards > New Dashboard > Configure > Import Dashboard JSON** y pega `observability/datadog/dashboard.json`.
* **Monitores:** en **Monitors > New Monitor > Import**, importa cada objeto de `observability/datadog/monitors.json` (están acotados a `env:production` para que el tráfico local no dispare alertas).
