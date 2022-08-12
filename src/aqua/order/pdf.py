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

import asyncio
import os.path
import re
import subprocess
from contextlib import asynccontextmanager
from functools import partial
from tempfile import TemporaryDirectory
from typing import AsyncIterator, BinaryIO, List, TextIO

from .html import format_size
from .types import OrderArticle, SupplierInfo


def _tex_escape(m: re.Match) -> str:
    badchar = m[0]
    try:
        # this way we preserve whitespaces
        return {
            "~": r"{\textasciitilde}",
            "^": r"{\textasciicircum}",
            "\\": r"{\textbackslash}",
            "₂": r"\textsubscript{2}",
            "\n": "\\\\\n",
            "\u00D7": r"{\texttimes}",
            "\u2007": r"\phantom{0}",
            "\u2008": r"\phantom{,}",
        }[badchar]
    except KeyError:
        return "\\" + badchar


tex_escape = partial(re.compile(r"[&%$#_{}~^\\₂\n\u00D7\u2007\u2008]").sub, _tex_escape)


def write_order_tex(
    fp: TextIO,
    articles: List[OrderArticle],
    date: str,
    info: SupplierInfo,
) -> None:
    fp.write(
        r"""\documentclass[a4paper,oneside,11pt]{article}
\usepackage[
    top=15mm,
    left=20mm,
    right=20mm,
    bottom=20mm,
]{geometry}
\usepackage[ngerman]{babel}
\usepackage[default]{opensans}
\usepackage{longtable}
\setlength{\parskip}{1em}
\setlength{\parindent}{0em}
\begin{document}
\textbf{"""
    )
    fp.write(tex_escape(info["name"]))
    fp.write(
        r"""}

\parbox[t]{.5\linewidth}{"""
    )
    fp.write(tex_escape(info["from_address"]))
    fp.write(
        r"""}%
\parbox[t]{.5\linewidth}{\raggedleft Lieferdatum: """
    )
    fp.write(tex_escape(date))
    fp.write(
        r"""}

St.-Nr.: """
    )
    fp.write(tex_escape(info["tax_id"]))
    fp.write(
        r"""\\
Kd.-Nr.: """
    )
    fp.write(tex_escape(str(info["customer_id"])))
    fp.write(
        r"""

"""
    )
    fp.write(tex_escape(info["from_name"]))
    fp.write(": ")
    fp.write(tex_escape(info["from_phone"]))
    fp.write(
        r"""

\begin{center}
    \begin{longtable}{c l c c}
        \hline
        \textbf{Artikel-Nr.} & \textbf{Artikel} & \textbf{Gebinde} & \textbf{Menge} \\
        \hline
    \endhead
"""
    )
    for article in articles:
        fp.write(r"        ")
        fp.write(tex_escape(article.get("id", "")))
        fp.write(r" & ")
        fp.write(tex_escape(article["name"]))
        fp.write(r" & ")
        fp.write(tex_escape(format_size(article.get("size"))))
        fp.write(r" & ")
        fp.write(tex_escape(article["amount"]))
        fp.write(
            r""" \\
"""
        )
    fp.write(
        r"""        \hline
    \end{longtable}
\end{center}

Mit freundlichen Grüßen\\
"""
    )
    fp.write(tex_escape(info["from_name"]))
    fp.write(
        r"""
\end{document}
"""
    )


async def run_latex(dir: str, name: str, timeout: int = 30) -> None:
    with open(os.path.join(dir, ".log"), "x+b") as fp:
        proc = await asyncio.create_subprocess_exec(
            "latexmk", name, cwd=dir, stdin=subprocess.DEVNULL, stdout=fp, stderr=fp
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout)
        except asyncio.TimeoutError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=1)
            except asyncio.TimeoutError:
                proc.kill()
            raise
        if proc.returncode != 0:
            fp.seek(0)
            raise ChildProcessError(fp.read().decode("utf-8", "surrogateescape"))


@asynccontextmanager
async def create_order_pdf(
    articles: List[OrderArticle], date: str, info: SupplierInfo
) -> AsyncIterator[BinaryIO]:
    with TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, ".latexmkrc"), "x", encoding="utf-8") as fp:
            fp.write(
                r"""$pdf_mode = 5;
$go_mode = 1;
"""
            )
        with open(os.path.join(tmp, "order.tex"), "x", encoding="utf-8") as fp:
            write_order_tex(fp, articles, date, info)
        await run_latex(tmp, "order.tex")
        with open(os.path.join(tmp, "order.pdf"), "rb") as fp:
            yield fp
