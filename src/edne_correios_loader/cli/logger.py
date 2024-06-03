import logging
from typing import ClassVar

import click


class ColorFormatter(logging.Formatter):
    colors: ClassVar[dict] = {
        "DEBUG": {"fg": "blue"},
        "WARNING": {"fg": "yellow"},
        "ERROR": {"fg": "red"},
        "CRITICAL": {"fg": "red"},
    }

    def formatMessage(self, record):  # noqa: N802
        level = record.levelname.upper()

        msg = record.getMessage()

        indentation = getattr(record, "indentation", None)
        msg = "\n".join("  " * (indentation or 0) + x for x in msg.splitlines())

        if level in self.colors:
            prefix = click.style(f"{level}: ", **self.colors[level])
            msg = "\n".join(prefix + x for x in msg.splitlines())

        if indentation == 0:
            msg = f"\n{msg}"

        return msg


class ClickHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            is_error = record.levelname.upper() in [
                "WARNING",
                "ERROR",
                "CRITICAL",
            ]
            click.echo(msg, err=is_error)
        except Exception:
            self.handleError(record)


_default_handler = ClickHandler()
_default_handler.formatter = ColorFormatter()


def configure_logger(logger):
    logger.handlers = [_default_handler]
    logger.propagate = False


def add_verbose_option(loggers):
    """
    A decorator that adds a `--verbose, -v` option to the decorated command and
    configure adds a handler to the logger.
    """

    for logger in loggers:
        configure_logger(logger)

    def decorator(f):
        def set_level(ctx, param, value):  # noqa:ARG001
            for logger in loggers:
                if value:
                    logger.setLevel(logging.DEBUG)
                else:
                    logger.setLevel(logging.INFO)

            return value

        return click.option(
            "--verbose",
            "-v",
            callback=set_level,
            is_flag=True,
            default=False,
            help="Enables verbose mode.",
        )(f)

    return decorator
