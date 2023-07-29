import datetime
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from tomllib import load

from sphinx.application import Sphinx

PACKAGE_NAME = "media_parser"
BASE_PATH = Path(__file__).resolve().parent.parent
SPHINX_SOURCE_PATH = BASE_PATH / "docs"

with (BASE_PATH / "pyproject.toml").open("rb") as f:
    poetry = load(f)["tool"]["poetry"]

REPO = poetry.get("repository", "")

SRC_PATH = BASE_PATH / PACKAGE_NAME

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
                '8c0-4.42-3.58-8-8-8z"></path>'
                "</svg>"
            ),
            "class": "",
        },
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

myst_enable_extensions = ["fieldlist", "deflist", "attrs_block", "tasklist", "attrs_inline"]
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

import autodoc2.sphinx.extension
from autodoc2.sphinx.extension import run_autodoc_package
from autodoc2.sphinx.utils import load_config


def run_autodoc(app: Sphinx) -> None:
    """The primary sphinx call back event for sphinx."""
    config = load_config(app)
    top_level_modules = []
    for i, _ in enumerate(config.packages):
        mod_path = run_autodoc_package(app, config, i)
        if mod_path is not None:
            top_level_modules.append(mod_path)
    # create the index page
    if top_level_modules and config.index_template:
        import jinja2

        content_str = jinja2.Template(config.index_template).render(top_level=top_level_modules)
        index_path = Path(app.srcdir) / PurePosixPath(config.output_dir) / autodoc2_index_filename
        if not (index_path.exists() and index_path.read_text("utf8") == content_str):
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(content_str, "utf8")


autodoc2.sphinx.extension.run_autodoc = run_autodoc


def setup(app: Sphinx):
    from pygments.lexers import JsonLexer

    app.add_lexer("json5", JsonLexer)
    app.connect("builder-inited", parser_config)


def parser_config(_: Sphinx):
    sys.path.append(SRC_PATH.as_posix())
    sys.path.append(BASE_PATH.as_posix())
    print(SRC_PATH, SRC_PATH.exists(), file=sys.stderr)

    from media_parser.models import ParserType
    from media_parser.parsers import BaseParser

    config: dict = json.loads(BaseParser.generate_schema())["properties"]

    text = [
        "# Parsers Configuration",
        "",
    ]

    for parser_type, params in config.items():
        text.append(
            f"## [{ParserType[parser_type.upper()].value}]"
            f"(#media_parser.models.medias.ParserType.{parser_type.upper()})"
        )
        text.append("")
        text.append(params["description"])
        text.append("")
        text.append(f"**Key**: `{parser_type}`")
        text.append("")
        text.append("**Properties**:")
        text.append("")
        if not params["properties"]:
            text.append("Does not have any properties.")
            text.append("")
            text.append("----")
            text.append("")
            continue

        required = params.get("required", [])
        for name, value in params["properties"].items():
            text.append(f"``````{{object}} {name}")

            if name in required:
                text.append(f"**This field is required to enable `{parser_type}` parser!**")
                text.append("")

            text.append(value.get("description", ""))
            text.append("")
            text.append(f"**type**: `{type_to_string(value['type'])}`{{l=python}}")
            text.append("")
            ph = type("placeholder", (), {})
            default = value.get("default", ph)

            if default is not ph:
                text.append(f"**default**: `{default!r}`{{l=python}}")
            text.append("``````")
            text.append("")
        text.append("")
        text.append("----")
        text.append("")
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
