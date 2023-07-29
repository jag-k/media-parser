# Client Usage

## Installation

The easiest way to install the package:

````{tab} pip
```bash
pip install media-parser
```
````

````{tab} pipx
```bash
pipx install media-parser
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
from media_parser import Client, FeedbackTypes

client = Client(url="http://localhost:8000")


async def main():
    # Get all media
    media = await client.parse("https://youtu.be/dQw4w9WgXcQ", user="jag-k")
    print(media)

    # If media is incorrect, you can send feedback
    await client.send_feedback(media, "jag-k", FeedbackTypes.wrong_media)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
```

For more info check {class}`media_parser.client.Client`
