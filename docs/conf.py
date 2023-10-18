import datetime
import json
import os
import re
import sys
from pathlib import Path
from tomllib import load

import yaml
from sphinx.application import Sphinx

PACKAGE_NAME = "media_parser"
SPHINX_SOURCE_PATH = Path(__file__).resolve().parent
BASE_PATH = SPHINX_SOURCE_PATH.parent
SPEC_PATH = SPHINX_SOURCE_PATH / "specs"
SPEC_PATH.mkdir(exist_ok=True, parents=True)

with (BASE_PATH / "pyproject.toml").open("rb") as f:
    poetry = load(f)["tool"]["poetry"]

REPO = poetry.get("repository", "")
PROJECT_NAME = poetry.get("name", "media_parser")

SRC_PATH = BASE_PATH / PACKAGE_NAME

sys.path.append(BASE_PATH.as_posix())
sys.path.append(SRC_PATH.as_posix())

project = "Media Parser"
full_author = poetry.get("authors", ["Jag_k"])[0]
author = full_author.split("<")[0].strip()
copyright = f"{datetime.date.today().year}, {author}"
release = poetry.get("version", "0.0.0")
version = release


extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx_copybutton",
    "sphinxext.opengraph",
    # "sphinxcontrib.openapi",
    # "sphinxcontrib.redoc",
    # "swagger_plugin_for_sphinx",
    "sphinx_inline_tabs",
    "sphinx.ext.duration",
    "sphinx.ext.coverage",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

templates_path = [(SPHINX_SOURCE_PATH / "_templates").as_posix()]
exclude_patterns = [".*", "requirements.txt"]

source_suffix = {
    ".md": "markdown",
}

html_theme = "furo"
html_logo = (SPHINX_SOURCE_PATH / "_static" / "logo.png").as_posix()
html_static_path = [(SPHINX_SOURCE_PATH / "_static").as_posix()]
html_search_options = {"type": "default"}
html_theme_options = {
    "navigation_with_keys": True,
    "footer_icons": [
        {
            "name": "GitHub",
            "url": REPO,
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">'
                '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
                "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53"
                ".63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 "
                "0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 "
                ".27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95"
                ".29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 "
                '8c0-4.42-3.58-8-8-8z"></path></svg>'
            ),
            "class": "",
        },
        # {
        #     "name": "Dash Docset",
        #     "url": f"/_static/{PROJECT_NAME}.zip",
        #     "html": '<img src="https://kapeli.com/img/dash-hr.png" width="30" height="28">',
        #     "class": "",
        # },
    ],
    "source_repository": REPO,
    "source_branch": "main",
    "source_directory": "docs/source",
}

ogp_site_url = os.getenv("READTHEDOCS_CANONICAL_URL", poetry["documentation"])
# ogp_image = "_static/og.png"
ogp_social_cards = {
    "enable": True,
    "line_color": "#B165AB",
}
ogp_type = "article"
ogp_enable_meta_description = True


# rst_prolog = "> {sub-ref}`today` | {sub-ref}`wordcount-words` words | {sub-ref}`wordcount-minutes` min read"

# python_display_short_literal_types = True
# python_use_unqualified_type_names = True

myst_enable_extensions = [
    "fieldlist",
    "deflist",
    "attrs_block",
    "tasklist",
    "attrs_inline",
]
myst_number_code_blocks = ["python"]
myst_heading_anchors = 3


AUTODOC2_RELATIVE_PATH = f"../{PACKAGE_NAME}"

autodoc2_hidden_objects = ["dunder", "private", "inherited"]
autodoc2_packages = [
    {
        "path": f"{AUTODOC2_RELATIVE_PATH}/models",
        "module": f"{PACKAGE_NAME}.models",
    },
    {
        "path": f"{AUTODOC2_RELATIVE_PATH}/client.py",
        "module": f"{PACKAGE_NAME}.client",
    },
]
autodoc2_render_plugin = "myst"

# language=Markdown
autodoc2_index_template = """# API Reference

This page contains auto-generated API reference documentation [^1].

```{toctree}
:titlesonly: true

{% for package in top_level %}
{{ package }}
{%- endfor %}
```

[^1]: Created with [sphinx-autodoc2](https://github.com/chrisjsewell/sphinx-autodoc2)"""

# https://github.com/sphinx-extensions2/sphinx-autodoc2/pull/29
autodoc2_index_filename = "index.md"


def setup(app: Sphinx):
    from main import app as _app
    from pygments.lexers.data import JsonLexer

    app.add_lexer("json5", JsonLexer)
    app.connect("builder-inited", parser_config)
    api = _app.openapi()
    with (SPEC_PATH / "openapi.json").open("w", encoding="utf-8") as f:
        json.dump(api, f, ensure_ascii=False, indent=2)
    with (SPEC_PATH / "openapi.yml").open("w", encoding="utf-8") as f:
        yaml.dump(api, f, allow_unicode=True)


def parser_config(_: Sphinx):
    from media_parser.models import ParserType
    from media_parser.parsers import BaseParser

    config: dict = json.loads(BaseParser.generate_schema())["properties"]

    text = [
        "# Parsers Configuration",
        "",
    ]

    for parser_type, params in config.items():
        text += [
            f"## [{ParserType[parser_type.upper()].value}]"
            f"(#media_parser.models.medias.ParserType.{parser_type.upper()})",
            "",
            params["description"],
            "",
            f"**Key**: `{parser_type}`",
            "",
            "**Properties**:",
            "",
        ]

        if not params["properties"]:
            text += [
                "Does not have any properties.",
                "",
                "----",
                "",
            ]

            continue

        required = params.get("required", [])
        for name, value in params["properties"].items():
            text.append(f"``````{{object}} {name}")

            if name in required:
                text += [
                    f"**This field is required to enable `{parser_type}` parser!**",
                    "",
                ]
            text += [
                value.get("description", ""),
                "",
                f"**type**: `{type_to_string(value['type'])}`{{l=python}}",
                "",
            ]
            ph = type("placeholder", (), {})
            default = value.get("default", ph)

            if default is not ph:
                text.append(f"**default**: `{default!r}`{{l=python}}")
            text += [
                "``````",
                "",
            ]
        text += [
            "",
            "----",
            "",
        ]
    path = SPHINX_SOURCE_PATH / "apidocs" / "parsers-config.md"
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(re.sub(r"\n{3,}", "\n\n", "\n".join(text[:-2])))


def type_to_string(type_: str) -> str:
    if type_ == "array":
        return "list"
    if type_ == "integer":
        return "int"
    if type_ == "number":
        return "float"
    if type_ == "boolean":
        return "bool"
    if type_ == "object":
        return "dict"
    if type_ == "string":
        return "str"
    return type_


swagger = [
    {
        "name": "Service API",
        "page": "openapi",
        "id": "my-page",
        "options": {
            "url": "specs/openapi.yml",
        },
    }
]

redoc_uri = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"

redoc = [
    {
        # "name": "Media API",
        "page": "usage/api",
        "spec": "specs/openapi.json",
        "embed": True,
        "opts": {"hide-hostname": True, "hide-loading": True},
    }
]
