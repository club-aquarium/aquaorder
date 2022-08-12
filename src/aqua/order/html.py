"""
aquaorder
Copyright (C) 2022  schnusch

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import importlib.resources
import re
from itertools import cycle
from typing import Callable, List, Mapping, Optional, Tuple, Union

import jinja2

from . import resources
from .types import ArticleChoices


def format_size(size: Union[None, int, float, str]) -> str:
    if not size:
        return ""
    figspace = "\u2007"
    parts = [x.strip() for x in str(size).rsplit("x", 2)]
    m = re.match(r"^(\d+)(?:[.,](\d+))?$", parts[-1])
    if m:
        if len(parts) == 1:
            parts.insert(0, "1")
        parts[-1] = m[1].rjust(2, figspace)
        parts[-1] += (("," + m[2]) if m[2] else "\u2008").ljust(3, figspace)
    if len(parts) > 1:
        parts[-2] = parts[-2].rjust(2, figspace)
    return " \u00D7 ".join(parts)


class ImportlibLoader(jinja2.BaseLoader):
    def get_source(
        self, environment: jinja2.Environment, template: str
    ) -> Tuple[str, Optional[str], Optional[Callable[[], bool]]]:
        source = importlib.resources.read_text(resources, template, encoding="utf-8")
        return (source, None, lambda: True)


loader = ImportlibLoader()
environment = jinja2.Environment(
    enable_async=True,
    loader=loader,
    auto_reload=True,
    autoescape=True,
)
environment.globals.update(
    {
        "format_size": format_size,
        "isinstance": isinstance,
        "len": len,
        "sorted": sorted,
        "title": "aquaorder",
    }
)


def get_all_suppliers(articles: List[List[ArticleChoices]]) -> Mapping[str, str]:
    suppliers = {}
    for section in articles:
        for article_choices in section:
            for supplier, article in article_choices.items():
                if isinstance(article, dict):
                    suppliers[supplier] = ""
    for supplier, color in zip(
        sorted(suppliers), cycle(["#ffdfdf", "#dfdfff", "#dfffdf"])
    ):
        suppliers[supplier] = color
    return suppliers


async def index(articles: List[List[ArticleChoices]]) -> bytes:
    return (
        await environment.get_template("index.html").render_async(
            articles=articles, suppliers=get_all_suppliers(articles)
        )
    ).encode("utf-8")
