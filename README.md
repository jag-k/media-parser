# Media Parser Server

Server for parse Media by URL.

## Supported medias

- [x] Youtube
- [x] Tiktok
- [x] Instagram
- [x] Twitter
- [x] Reddit
- [ ] Pinterest

## Installation and Configuration

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
this: [schemas/parser_schema.json](schemas/parser_schema.json).

For enable parser, you need to add config for this parser.
If parser haven't config, like `tiktok` set empty object (`{}`) to enable it.

Example:

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
    "twitter_bearer_token": ""
  },
  "youtube": {}
}
```

## Usage

API documentation available on `/docs` endpoint.

### Clients

Python client for this server available on [@jag-k/media-parser-client](https://github.com/jag-k/media-parser-client)

## License

[MIT](LICENSE)
