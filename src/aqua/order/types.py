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

from typing import Mapping, TypedDict, Union

ArticleSchema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "id": {
            "oneOf": [
                {"type": "number"},
                {"type": "string"},
            ],
        },
        "size": {
            "oneOf": [
                {"type": "number"},
                {"type": "string"},
            ],
        },
    },
    "required": ["name"],
}


class _Article(TypedDict, total=True):
    name: str


class Article(_Article, total=False):
    id: Union[int, float, str]
    size: Union[int, float, str]


ArticleChoicesSchema = {
    "type": "object",
    "properties": {
        "hint": {"type": "string"},
    },
    "additionalProperties": ArticleSchema,
}


class _ArticleChoices(TypedDict, total=False):
    hint: str


ArticleChoices = Union[_ArticleChoices, Mapping[str, Article]]


OrderArticleSchema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "size": {"type": "string"},
        "amount": {"type": "string"},
    },
    "required": ["name", "size"],
}


class _OrderArticle(TypedDict, total=True):
    name: str
    amount: str


class OrderArticle(_OrderArticle, total=False):
    id: str
    size: str


SupplierInfoSchema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "customer_id": {
            "oneOf": [
                {"type": "number"},
                {"type": "string"},
            ],
        },
        "tax_id": {"type": "string"},
        "from_address": {"type": "string"},
        "from_name": {"type": "string"},
        "from_phone": {"type": "string"},
    },
    "required": [
        "name",
        "customer_id",
        "tax_id",
        "from_address",
        "from_name",
        "from_phone",
    ],
}


class SupplierInfo(TypedDict, total=True):
    name: str
    customer_id: Union[int, float, str]
    tax_id: str
    from_address: str
    from_name: str
    from_phone: str
