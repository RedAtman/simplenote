import logging
from pprint import pformat
from typing import Any, Dict, List, Tuple, Union


logger = logging.getLogger(__name__)

__all__ = ["json"]


json = lambda msg: pformat(msg, indent=1, width=80, depth=9)
try:
    from pygments import formatters, highlight, lexers

    def json(msg: Union[Dict[str, Any], List[Any], Tuple[Any], str, int, float, bool, None]) -> str:
        return highlight(
            pformat(msg, indent=1, width=80, depth=9),
            lexers.JsonnetLexer(),
            # lexers.JsonLexer(),
            # lexers.PythonTracebackLexer(),
            # formatters.TerminalTrueColorFormatter(
            #     # style="algol",
            #     # style="manni",
            #     # style="material",
            #     style="paraiso-dark",
            #     # style="dracula",
            #     # style="friendly",
            #     # style="github-dark",
            #     # style="gruvbox-dark",
            #     # style="gruvbox-light",
            #     # style="native",
            #     # style="rrt",
            #     # style="stata-light",
            #     # style="tango",
            #     # style="trac",
            #     # style="xcode",
            # ),
            # formatters.TerminalFormatter(
            #     bg="dark",
            #     style="paraiso-dark",
            # ),
            formatters.Terminal256Formatter(
                # style="colorful",
                # style="lightbulb",
                # style="material",
                style="nord",
                # style="staroffice",
                # style="zenburn",
            ),
            # formatters.TerminalFormatter(bg="dark"),
            # formatters.TerminalFormatter(bg="light"),
        )

except ImportError:
    logger.warning("Using default json lexer formatter. Install pygments `pip install pygments` for better output.")
    pass


if __name__ == "__main__":
    print(json("Hello, world!"))
    # print(output(output.__dict__))
    print(json(locals()))
