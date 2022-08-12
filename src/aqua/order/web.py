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

import argparse
import asyncio
import importlib.resources
import os.path
import pathlib
import re
import socket
import weakref
from contextlib import contextmanager
from functools import partial, reduce
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    Generic,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import jsonschema  # type: ignore
from aiohttp import web
from aiohttp.web_runner import AppRunner, BaseSite, SockSite, TCPSite, UnixSite
from yaml import load_all as yaml_load_all  # type: ignore

try:
    from yaml import CLoader as YamlLoader
except ImportError:
    from yaml import Loader as YamlLoader

from . import html, resources
from .pdf import create_order_pdf
from .types import (
    ArticleChoices,
    ArticleChoicesSchema,
    OrderArticle,
    SupplierInfo,
    SupplierInfoSchema,
)

try:
    import systemd.daemon  # type: ignore
except ImportError:
    systemd_imported = False

    def get_systemd_listen_sockets() -> List[socket.socket]:
        raise NotImplementedError

else:
    systemd_imported = True

    def get_systemd_listen_sockets() -> List[socket.socket]:
        socks = []
        for fd in systemd.daemon.listen_fds():
            for family in (socket.AF_UNIX, socket.AF_INET, socket.AF_INET6):
                if systemd.daemon.is_socket(
                    fd, family=family, type=socket.SOCK_STREAM, listening=True
                ):
                    sock = socket.fromfd(fd, family, socket.SOCK_STREAM)
                    socks.append(sock)
                    break
            else:
                raise RuntimeError(
                    "socket family must be AF_INET, AF_INET6, or AF_UNIX; "
                    "socket type must be SOCK_STREAM; and it must be listening"
                )
        return socks


T = TypeVar("T")


class YAMLLoader(Generic[T]):
    class WeakList(list):
        pass

    def __init__(self, name: str):
        self.name = name  # type: Final[str]
        self.mtime = None  # type: Union[None, int, float]
        self.get_cached = lambda: None  # type: Callable[[], Optional[List[T]]]

    def validate(self, section: T) -> None:
        pass

    def __call__(self) -> List[T]:
        sections = self.get_cached()
        mtime = os.path.getmtime(self.name)
        if sections is None or self.mtime is None or mtime > self.mtime:
            sections = []
            with open(self.name, "r", encoding="utf-8") as fp:
                for section in yaml_load_all(fp, Loader=YamlLoader):
                    self.validate(section)
                    sections.append(cast(T, section))
            self.get_cached = weakref.ref(self.WeakList(sections))
            self.mtime = mtime
        return sections


class ArticleLoader(YAMLLoader[List[ArticleChoices]]):
    def validate(self, section: Any) -> None:
        assert isinstance(section, list)
        for article_choices in section:
            jsonschema.validate(article_choices, ArticleChoicesSchema)


class SupplierLoader(YAMLLoader[Mapping[str, SupplierInfo]]):
    def validate(self, section: Any) -> None:
        assert isinstance(section, dict)
        for supplier, supplier_info in section.items():
            assert isinstance(supplier, str)
            jsonschema.validate(supplier_info, SupplierInfoSchema)


async def index(
    load_articles: ArticleLoader, request: web.Request
) -> web.StreamResponse:
    articles = load_articles()
    body = await html.index(articles)
    return web.Response(body=body, headers={"Content-Type": "application/xhtml+xml"})


async def file(path: pathlib.Path, request: web.Request) -> web.StreamResponse:
    return web.FileResponse(path=path)


async def get_structured_order_data(
    raw_data: Mapping[str, str]
) -> Mapping[str, List[OrderArticle]]:
    data = {}  # type: Dict[str, List[OrderArticle]]
    for key, amount in raw_data.items():
        m = re.match(r"^(\d+)_amount$", key)
        if m is None or not amount or amount == "0":
            continue
        i = m[1]
        try:
            supplier = raw_data[f"{i}_supplier"]
            name = raw_data[f"{i}_{supplier}_name"]
        except KeyError:
            raise web.HTTPBadRequest(
                text=f"missing {i}_supplier or {i}_{supplier}_name"
            )

        article = OrderArticle(name=name, amount=amount)
        data.setdefault(supplier, []).append(article)
        try:
            article["id"] = raw_data[f"{i}_{supplier}_id"]
        except KeyError:
            pass
        try:
            article["size"] = raw_data[f"{i}_{supplier}_size"]
        except KeyError:
            pass

    return data


async def order(
    load_suppliers: SupplierLoader, request: web.Request
) -> web.StreamResponse:
    raw_data = cast(Mapping[str, str], await request.post())
    if not raw_data:
        raise web.HTTPBadRequest
    try:
        supplier = raw_data["supplier"]
        date = raw_data["date"]
    except KeyError:
        raise web.HTTPBadRequest(text="missing supplier or date")

    orders = await get_structured_order_data(raw_data)
    try:
        order = orders[supplier]
    except KeyError:
        raise web.HTTPBadRequest(text=f"order for supplier {supplier} not found")

    supplier_infos = reduce(
        dict.__or__, load_suppliers(), {}
    )  # type: Dict[str, SupplierInfo]
    try:
        info = supplier_infos[supplier]
    except KeyError:
        raise web.HTTPBadRequest(text=f"supplier info for {supplier} not found")

    async with create_order_pdf(order, date, info) as fp:
        size = os.stat(fp.fileno()).st_size
        resp = web.StreamResponse()
        resp.content_type = "application/pdf"
        resp.content_length = size
        await resp.prepare(request)
        while size > 0:
            x = fp.read(max(64 * 1024, size))
            if not x:
                break
            await resp.write(x)
            size -= len(x)
        await resp.write_eof()
        return resp


@contextmanager
def create_app(
    load_articles: ArticleLoader,
    load_suppliers: SupplierLoader,
) -> Iterator[web.Application]:
    app = web.Application()
    with importlib.resources.path(resources, "style.css") as style_css:
        app.router.add_routes(
            [
                web.get("/", partial(index, load_articles)),
                web.get("/style.css", partial(file, style_css)),
                web.post("/order{tail:(/.*)?}", partial(order, load_suppliers)),
            ]
        )
        yield app


ListenAddress = Union[str, Tuple[str, int], socket.socket]


def listen_address(arg: str) -> ListenAddress:
    socket = r"(?P<socket>.*/.*)"
    ipv6 = r"\[(?P<ipv6>.*)\]"
    host = r"(?P<host>.*)"
    port = r":(?P<port>\d+)"
    m = re.match(f"^(?:{socket}|(?:(?:{ipv6}|{host}){port}))$", arg)
    if m is None:
        raise ValueError
    if m["port"]:
        portnum = int(m["port"], 10)
        host = m["ipv6"] or m["host"]
        return (host, portnum)
    else:
        return m["socket"]


async def real_main(
    load_articles: ArticleLoader,
    load_suppliers: SupplierLoader,
    listen_addresses: List[ListenAddress],
) -> None:
    assert listen_addresses
    with create_app(load_articles, load_suppliers) as app:
        runner = AppRunner(app)
        await runner.setup()
        try:
            sites = []  # type: List[BaseSite]
            for address in listen_addresses:
                if isinstance(address, socket.socket):
                    sites.append(SockSite(runner, address))
                elif isinstance(address, str):
                    sites.append(UnixSite(runner, address))
                else:
                    host, port = address
                    sites.append(TCPSite(runner, host, port))
            for site in sites:
                await site.start()

            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            pass
        finally:
            await runner.cleanup()


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(
        description="...",
        epilog=None
        if systemd_imported
        else "systemd socket activations cannot be used, because systemd.daemon could not be imported, see https://github.com/systemd/python-systemd",
    )
    p.add_argument(
        "--articles",
        required=True,
        help="YAML file to load articles from",
    )
    p.add_argument(
        "--suppliers",
        required=True,
        help="YAML file to load supplier infos from",
    )
    g = p.add_mutually_exclusive_group(required=True)
    if systemd_imported:
        g.add_argument(
            "--systemd",
            action="store_true",
            help="receive listening sockets from systemd",
        )
    g.add_argument(
        "-l", "--listen", type=listen_address, action="append", help="listening address"
    )
    args = p.parse_args(argv)

    if systemd_imported and args.systemd:
        if not systemd.daemon.booted():
            p.error("systemd not running")
        listen = cast(List[ListenAddress], get_systemd_listen_sockets())
        if not listen:
            p.error("no sockets received from systemd")
    else:
        listen = args.listen

    asyncio.run(
        real_main(
            ArticleLoader(args.articles),
            SupplierLoader(args.suppliers),
            listen,
        )
    )
