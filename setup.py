import sys
import subprocess
from setuptools import setup  # type: ignore
from setuptools.command.build_py import build_py  # type: ignore


def run(*args: str) -> None:
    print(*args, file=sys.stderr)
    subprocess.run(args, check=True)


class BuildPyCommand(build_py):
    def run(self) -> None:
        run(
            "sassc",
            "src/style.scss",
            "src/aqua/order/resources/style.css",
        )
        super().run()


setup(cmdclass={"build_py": BuildPyCommand})
