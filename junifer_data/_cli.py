"""CLI for junifer-data."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
import pathlib

import click

from . import _functions as cli_func


__all__ = ["cli", "download", "drop", "get"]


def _set_log_config(verbose: int) -> None:
    """Set logging config.

    Parameters
    ----------
    verbose : int
        Verbosity.

    """
    # Configure logger based on verbosity
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logging.getLogger("junifer-data").setLevel(level)
    logging.getLogger("datalad").setLevel(level)


@click.group
@click.version_option()
@click.help_option()
def cli() -> None:  # pragma: no cover
    """junifer-data CLI client."""


@cli.command
@click.argument(
    "file_path",
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "-d",
    "--dataset_path",
    default=None,
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    metavar="<dataset>",
    help="Path to dataset",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=str,
    metavar="<tag>",
    help="Tag to checkout",
)
@click.option(
    "-s",
    "--hexsha",
    default=None,
    type=str,
    metavar="<hexsha>",
    help="Commit hash to verify",
)
@click.option("-v", "--verbose", count=True, type=int)
def get(
    file_path: click.Path,
    dataset_path: click.Path,
    tag: str,
    hexsha: str,
    verbose: int,
) -> None:
    """Get FILE_PATH.

    FILE_PATH should be relative to <dataset>/<tag>, if provided.
    If not provided, <dataset> defaults to "$HOME/junifer_data/<tag>" and <tag>
    defaults to "main". If <hexsha> is provided, commit hash is verified.

    """
    _set_log_config(verbose)
    try:
        path = cli_func.get(
            file_path=file_path,
            dataset_path=dataset_path,
            tag=tag,
            hexsha=hexsha,
        )
    except RuntimeError as err:
        click.echo(f"Failure: {err}", err=True)
    else:
        click.echo(f"Success: {path.resolve()}")


@cli.command
@click.argument(
    "dataset_path",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
)
@click.option("-v", "--verbose", count=True, type=int)
def drop(
    dataset_path: click.Path,
    verbose: int,
) -> None:
    """Drop DATASET_PATH."""
    _set_log_config(verbose)
    try:
        cli_func.drop(dataset_path=dataset_path)
    except RuntimeError as err:
        click.echo(f"Failure: {err}", err=True)
    else:
        click.echo("Success")


@cli.command
@click.option(
    "-d",
    "--dataset_path",
    default=None,
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    metavar="<dataset>",
    help="Path to dataset",
)
@click.option(
    "-t",
    "--tag",
    default=None,
    type=str,
    metavar="<tag>",
    help="Tag to checkout",
)
@click.option("-v", "--verbose", count=True, type=int)
def download(
    dataset_path: click.Path,
    tag: str,
    verbose: int,
) -> None:
    """Download complete dataset.

    If not provided, <dataset> defaults to "$HOME/junifer_data/<tag>" and <tag>
    defaults to "main".

    """
    _set_log_config(verbose)
    try:
        path = cli_func.get(
            file_path=pathlib.Path("."),
            dataset_path=dataset_path,
            tag=tag,
        )
    except RuntimeError as err:
        click.echo(f"Failure: {err}", err=True)
    else:
        click.echo(f"Success: {path.resolve()}")
