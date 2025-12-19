# Lab Alert Middleware

A FastAPI-based webhook adapter that converts **Prometheus Alertmanager** and **Home Assistant** notifications into stylish Discord embeds.

## Configuration

The application is configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | **Required** Discord Webhook URL | None |
| `HOST` | Host to bind the server to | `0.0.0.0` |
| `PORT` | Port to run the server on | `5001` |

### Docker

#### Using the pre-built image (Recommended)

The image is automatically published to GHCR and supports both `amd64` and `arm64` architectures. You can use it directly in your `docker-compose.yml` or Ansible playbooks:

```yaml
services:
  app:
    image: ghcr.io/agusespa/lab-alert-middleware:latest
    ports:
      - "5001:5001"
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
```

#### Local Build

Build and run with Docker Compose:
```bash
DISCORD_WEBHOOK_URL=your_url docker-compose up -d --build
```

## API Endpoints

- `POST /webhook/alertmanager`: Receives Alertmanager payloads (backward compatible with `/webhook`).
- `POST /webhook/homeassistant`: Receives Home Assistant payloads.
- `GET /health`: Health check endpoint.
- `GET /docs`: Automatic OpenAPI documentation.

## Home Assistant Integration

You can send notifications from Home Assistant using a `RESTful Command`:

```yaml
rest_command:
  discord_notification:
    url: "http://your-middleware-ip:5001/webhook/homeassistant"
    method: POST
    payload: '{"title": "{{ title }}", "message": "{{ message }}", "data": {"severity": "{{ severity | default("info") }}"}}'
    content_type: "application/json"
```

### Sample JSON Payload

If you are using `curl` or another tool, the expected JSON format is:

```json
{
  "title": "Battery Low",
  "message": "The front door lock battery is at 10%",
  "data": {
    "severity": "warning"
  }
}
```

### Payload Specification

| Field | Description | Default |
|-------|-------------|---------|
| `title` | Notification title | `Home Assistant Notification` |
| `message` | Notification body | `No message provided` |
| `data.severity` | `critical`, `warning`, `info` | `info` |

## Testing

Run tests using pytest:
```bash
DISCORD_WEBHOOK_URL=mock pytest
```