# Server Usage

## Installation

You can start server choosing one of the following options:

````{tab} Docker Compose (recommended)

```{admonition} Requirements

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
```

This is example of `docker-compose.yml` file:

{caption="docker-compose.yml"}
```yaml
version: '3.8'

services:
  app:
    image: "ghcr.io/jag-k/media-parser:latest"
    container_name: "media_parser"
    ports:
      - "8000:8000"
    environment:
      # Sentry integration (optional)
      SENTRY_DSN: "https://asdasda@sentry.io/2"
      SENTRY_ENVIRONMENT: "dev"

      # Enable sentry user feedback (optional)
      SENTRY_ORGANISATION_SLUG: "sentry"
      SENTRY_PROJECT_SLUG: "media-parser"
      SENTRY_AUTH_TOKEN: "asdasdasd"  # with scope project:write
      SENTRY_API_HOST: "https://sentry.io/"

      # Database
      MONGO_URL: "mongodb://user:password@mongodb:27017"
      MONGO_DATABASE: "media-parser"

    depends_on:
      - mongodb

    volumes:
      - ./config:/config

  mongodb:
    image: mongo:latest
    container_name: mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: "user"
      MONGO_INITDB_ROOT_PASSWORD: "password"
      MONGO_INITDB_DATABASE: "media-parser"
    volumes:
      - ./config/mongo:/data/db

    ports:
      - "27017:27017"
```
````

````{tab} docker run command

```{admonition} Requirements
:class: requirements

- [Docker](https://www.docker.com/)
- [MongoDB](https://www.mongodb.com/) - You can also use [MongoDB Docker image](https://hub.docker.com/_/mongo)
```

```bash
docker run -d \
  --name media_parser \
  -p 8000:8000 \
  -e SENTRY_DSN="https://asdasda@sentry.io/2" \  # optional
  -e SENTRY_ENVIRONMENT="dev" \  # optional
  -e SENTRY_ORGANISATION_SLUG="sentry" \  # optional
  -e SENTRY_PROJECT_SLUG="media-parser" \  # optional
  -e SENTRY_AUTH_TOKEN="asdasdasd" \  # optional
  -e SENTRY_API_HOST="https://sentry.io/" \  # optional
  -e MONGO_URL="mongodb://user:password@mongodb:27017" \
  -e MONGO_DATABASE="media-parser" \
  -v ./config:/config \
  ghcr.io/jag-k/media-parser:latest
```


Example of MongoDB Docker image:

```bash
docker run -d \
  --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME="user" \
  -e MONGO_INITDB_ROOT_PASSWORD="password" \
  -e MONGO_INITDB_DATABASE="media-parser" \
  -v ./config/mongo:/data/db \
  -p 27017:27017 \
  mongo:latest
```
````

````{tab} Manual install

```{admonition} Requirements
:class: requirements

- [Python 3.11](https://python.org/)
- [Poetry](https://python-poetry.org/) - For installing dependencies
- [MongoDB](https://www.mongodb.com/) - You can also use [MongoDB Docker image](https://hub.docker.com/_/mongo)
```

Clone the repository:
```bash
git clone https://github.com/jag-k/media-parser.git
```

Install dependencies:
```bash
poetry install --no-root
```

Run server:
```bash
cd media-parser && poetry run uvicorn media_parser.main:app
```
````

After that, you can open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

## Configuration

For run server you need to set environment variables and parser config files.

### Env Variables

{width=inherit}
| Name | Description | Required |
|----------------------------|--------------------------|----------|
| `MONGO_URL`                | MongoDB URL | `True`   |
| `MONGO_DATABASE`           | MongoDB database name | `True`   |
| `SENTRY_DSN`               | Sentry DSN | `False`  |
| `SENTRY_ENVIRONMENT`       | Sentry environment | `False`  |
| `SENTRY_ORGANISATION_SLUG` | Sentry organization slug | `False`  |
| `SENTRY_PROJECT_SLUG`      | Sentry project slug | `False`  |
| `SENTRY_AUTH_TOKEN`        | Sentry auth token | `False`  |
| `SENTRY_API_HOST`          | Sentry API host | `False`  |

### Parsers Config

To configure parsers, you need to create a config file.
JSON Schema for config file:
[schemas/parser_schema.json](https://github.com/jag-k/media-parser/blob/main/schemas/parser_schema.json).

To enable parser, you need to add config for this parser.
If parser hasn't config, like `tiktok` set an empty object (`{}`) to enable it.

Example of config file:

````{tab} YAML

`config/parsers.yaml` or `config/parsers.yml`

```yaml
# config/parsers.yml
$schema: "https://raw.github.com/jag-k/media-parsers/blob/main/schemas/parser_schema.json"
instagram:
    # Optional
    lamadava_saas_token: "asdasd"
reddit:
    client_id: ""
    client_secret: ""
    # Optional
    user_agent: "video downloader (by u/Jag_k)"
tiktok: {}
twitter:
    twitter_bearer_token: "asdasd"
youtube: {}
```
````

````{tab} JSON

`config/parsers.json`

```json5
{
    "$schema": "https://raw.github.com/jag-k/media-parsers/blob/main/schemas/parser_schema.json",
    "instagram": {
        // Optional
        "lamadava_saas_token": "asdasd"
    },
    "reddit": {
        "client_id": "",
        "client_secret": "",
        // Optional
        "user_agent": "video downloader (by u/Jag_k)"
    },
    "tiktok": {},
    "twitter": {
        "twitter_bearer_token": "asdasd"
    },
    "youtube": {}
}
```
````

You can find more information about parsers props config in [parsers config docs](../apidocs/parsers-config).

```{toctree}
:hidden:
:maxdepth: 2

../apidocs/parsers-config
```
