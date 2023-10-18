# Media Parser

[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Documentation Status](https://readthedocs.org/projects/media-parser/badge/?version=latest)](https://media-parser.readthedocs.io/?badge=latest)
[![Build Docker image](https://github.com/jag-k/media-parser/actions/workflows/docker-image.yml/badge.svg)](https://github.com/jag-k/media-parser/actions/workflows/docker-image.yml)
[![PyPI publish](https://github.com/jag-k/media-parser/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/jag-k/media-parser/actions/workflows/pypi-publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/media-parser?logo=pypi&label=media-parser)](https://pypi.org/project/media-parsers/)

Server for parse Media by URL.

## Supported medias

- [x] Youtube
- [x] Tiktok
- [x] Instagram
- [x] Twitter
- [x] Reddit
- [ ] Pinterest

## Installation and Configuration Server

Use the `docker-compose.yml` file to run the server.

```yaml
version: "3.8"

service:
    media-parser:
        image: ghcr.io/jag-k/media-parser:latest
        ports:
            - 8000:8000
        environment:
            # Sentry integration (optional)
            SENTRY_DSN: "https://abcabc@sentry.io/2"
            SENTRY_ENVIRONMENT: "dev"

            # Enable sentry user feedback (optional)
            SENTRY_ORGANISATION_SLUG: "sentry"
            SENTRY_PROJECT_SLUG: "media-parser"
            SENTRY_AUTH_TOKEN: "..."  # with scope project:write
            SENTRY_API_HOST: "https://api.sentry.io/"

            # Database
            MONGO_URL: "mongodb://mongodb:27017"
            MONGO_DATABASE: "test"

        volumes:
            - ./config:/config

    mongodb:
        image: mongo:latest
        volumes:
            - ./data:/data/db
```

### Parsers Configuration

All configs for parsers stored in `config/parsers.json`. JSON Schema for
this: [schemas/parser_schema.json](https://github.com/jag-k/media-parser/blob/main/schemas/parser_schema.json).

To enable parser, you need to add config for this parser.
If parser hasn't config, like `tiktok` set an empty object (`{}`) to enable it.

Example:

```json5
// config/parsers.json
{
    "$schema": "https://raw.github.com/jag-k/media-parsers/blob/main/schemas/parser_schema.json",
    "instagram": {
        // Optional
        "instagram_saas_token": "asdasd"
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

Or you can use YAML file like `config/parsers.yaml` or `config/parsers.yml`:

```yaml
# config/parsers.yml
$schema: "https://raw.github.com/jag-k/media-parsers/blob/main/schemas/parser_schema.json"
instagram:
    # Optional
    instagram_saas_token: "asdasd"
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

## Usage

API documentation available on `/docs` endpoint.

## Clients

### Installation

```bash
poetry add media-parser  # or pip install media-parser
```

### Usage

```python
from media_parser import Client, FeedbackTypes

client = Client(url="http://localhost:8000")


async def main():
    # Get all media
    media = await client.parse("https://www.youtube.com/watch?v=9bZkp7q19f0", user="jag-k")
    print(media)

    # If media is incorrect, you can send feedback
    await client.send_feedback(media, "jag-k", FeedbackTypes.wrong_media)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
```

## License

[MIT](https://github.com/jag-k/media-parser/blob/main/LICENSE)
