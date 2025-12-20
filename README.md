# Lab Alert Middleware

A FastAPI-based webhook adapter that converts incoming notifications into stylish Discord embeds. It's designed to be **service-agnostic**, meaning it can process alerts from any source that follows its simple unified format.

## Configuration

The application is configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | **Required** Discord Webhook URL | None |
| `HOST` | Host to bind the server to | `0.0.0.0` |
| `PORT` | Port to run the server on | `5001` |

### Docker

#### Using the pre-built image (Recommended)

The image is automatically published to GHCR and supports both `amd64` and `arm64` architectures.

```yaml
services:
  app:
    image: ghcr.io/agusespa/lab-alert-middleware:latest
    ports:
      - "5001:5001"
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
```

## API Endpoints

- `POST /discord-alert`: Posts formatted alerts to Discord. Accepts the **Unified Alert Format**.
- `GET /health`: Health check endpoint.

## Unified Alert Format

The middleware expects a JSON payload matching this structure:

```json
{
  "title": "CPUTemperature",
  "summary": "CPU temperature too high",
  "description": "CPU at 85°C on lab-pc-1",
  "severity": "critical",
  "status": "firing",
  "timestamp": "2023-12-20T08:00:00Z"
}
```

### Specification

| Field | Description | Default |
|-------|-------------|---------|
| `title` | **Required**. Main name of the alert. | None |
| `summary` | Optional*. Short one-line summary used as the main message. | None |
| `description` | Optional*. Detailed info shown in a separate field. | None |
| `severity` | `critical`, `warning`, `info` | `info` |
| `status` | `firing`, `resolved` | `firing` |
| `timestamp` | Optional. ISO8601 timestamp. | Current Time |

\* *At least one of `summary` or `description` must be provided. If both are missing, the alert will be rejected.*

## Usage Examples

### Generic Curl (Unified Format)
```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{"title": "Door Open", "summary": "Front door was opened", "severity": "warning"}'
```

### Home Assistant Integration
You can send notifications from Home Assistant using a `RESTful Command`:

```yaml
rest_command:
  alertmanager_middleware:
    url: "http://192.168.1.157:5001/discord-alert"
    method: POST
    content_type: 'application/json'
    payload: >
      {
        "title": "{{ title }}",
        "summary": "{{ summary | default(message) }}",
        "description": "{{ description | default('') }}",
        "severity": "{{ severity | default('info') }}",
        "status": "{{ status | default('firing') }}",
        "timestamp": "{{ timestamp | default(now().isoformat()) }}"
```