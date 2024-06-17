from pprint import pformat

from pygments import formatters, highlight, lexers


def output(msg):
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


if __name__ == "__main__":
    print(output("Hello, world!"))
    # print(output(output.__dict__))
    print(output(locals()))
