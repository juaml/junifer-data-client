"""Utilities for junifer-data."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path
from typing import Optional, Union

import datalad.api as dl
from datalad.runner.exception import CommandError
from datalad.support.exceptions import IncompleteResultsError


__all__ = ["check_dataset"]


logger = logging.getLogger(__name__)


def check_dataset(
    data_dir: Union[str, Path, None] = None,
    tag: Optional[str] = None,
) -> dl.Dataset:
    """Get or install junifer-data dataset.

    Parameters
    ----------
    data_dir: str or pathlib.Path or None, optional
        Path to the dataset. If None, defaults to
        ``"$HOME/junifer_data/{tag}"`` else
        ``"{data_dir}/{tag}"`` is used (default None).
    tag: str or None, optional
        Tag to checkout; for example, for ``v1.0.0``, pass ``"1.0.0"``.
        If None, ``"main"`` is checked out (default None).

    Returns
    -------
    datalad.api.Dataset
        The junifer-data dataset.

    Raises
    ------
    RuntimeError
        If there is a problem checking the dataset.

    """
    # Check tag
    if tag is not None:
        tag = f"v{tag}"
    else:
        tag = "main"

    # Set dataset location
    if data_dir is not None:
        data_dir = Path(data_dir) / tag
    else:
        data_dir = Path().home() / "junifer_data" / tag

    # Check if the dataset is installed at storage path;
    # else clone a fresh copy
    if dl.Dataset(data_dir).is_installed():
        logger.debug(f"Found existing junifer-data at: {data_dir.resolve()}")
        dataset = dl.Dataset(data_dir)
    else:
        logger.debug(f"Cloning junifer-data to: {data_dir.resolve()}")
        # Clone dataset
        try:
            dataset = dl.clone(
                "https://github.com/juaml/junifer-data.git",
                path=data_dir,
                result_renderer="disabled",
            )
        except IncompleteResultsError as e:
            raise RuntimeError(
                f"Failed to clone junifer-data: {e.failed}"
            ) from e
        else:
            logger.debug(
                f"Successfully cloned junifer-data to: {data_dir.resolve()}"
            )

    # Update dataset to stay up-to-date
    try:
        dataset.update()
    except CommandError as e:
        raise RuntimeError(f"Failed to update junifer-data: {e}") from e
    else:
        logger.debug("Successfully updated junifer-data")

    # Checkout correct state
    try:
        dataset.recall_state(tag)
    except CommandError as e:
        raise RuntimeError(
            f"Failed to checkout state of junifer-data: {e}"
        ) from e
    else:
        logger.debug("Successfully checked out state of junifer-data")

    return dataset
