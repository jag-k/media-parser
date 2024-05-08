# Use as package

## Installation

The easiest way to install the package:

````{tab} pip
```bash
pip install media-parser
```
````

````{tab} poetry
```bash
poetry add media-parser
```
````


## Code examples

{caption="main.py"}

```python
import aiohttp

from media_parser import BaseParser, Media

# More info you can find on "Parser Configuration" page
config = {
    "instagram": {},
    "tiktok": {},
    "youtube": {}
}

parser = BaseParser(config=config)


async def main():
    async with aiohttp.ClientSession() as session:
        media: list[Media] = await parser.parse(
            client=client,
            string="https://youtu.be/dQw4w9WgXcQ",
            cache_collection=None,
        )
    print(media)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
```
