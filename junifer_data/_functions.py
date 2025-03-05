"""Functions for junifer-data."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path
from typing import Optional

import datalad.api as dl
from datalad.runner.exception import CommandError
from datalad.support.exceptions import IncompleteResultsError, NoDatasetFound

from ._utils import check_dataset


__all__ = ["drop", "get"]


logger = logging.getLogger(__name__)


def get(
    file_path: Path,
    dataset_path: Optional[Path] = None,
    tag: Optional[str] = None,
    hexsha: Optional[str] = None,
) -> Path:
    """Fetch ``file_path`` from junifer-data dataset.

    Parameters
    ----------
    file_path : pathlib.Path
        File path (relative to ``"{dataset_path}/{tag}"``) to fetch.
    dataset_path : pathlib.Path or None, optional
        Path to the dataset. If None, defaults to
        ``"$HOME/junifer_data/{tag}"`` else
        ``"{dataset_path}/{tag}"`` is used (default None).
    tag : str or None, optional
        Tag to checkout; for example, for ``v1.0.0``, pass ``"1.0.0"``.
        If None, ``"main"`` is checked out (default None).
    hexsha: str or None, optional
        Commit hash to verify. If None, no verification will be performed.

    Returns
    -------
    pathlib.Path
        Resolved fetched file path.

    Raises
    ------
    RuntimeError
        If there is a problem fetching the file.
    ValueError
        If `hexsha` is provided but does not match the checked out tag.
        If `hexsha` is provided for the main tag.

    """
    # Get dataset
    dataset = check_dataset(data_dir=dataset_path, tag=tag, hexsha=hexsha)
    # Fetch file
    try:
        got = dataset.get(file_path, result_renderer="disabled")
    except IncompleteResultsError as e:
        raise RuntimeError(
            f"Failed to get file from dataset: {e.failed}"
        ) from e
    else:
        got_path = Path(got[0]["path"])
        # Conditional logging based on file fetch
        status = got[0]["status"]
        if status == "ok":
            logger.debug(f"Successfully fetched file: {got_path.resolve()}")
            return got_path
        elif status == "notneeded":
            logger.debug(f"Found existing file: {got_path.resolve()}")
            return got_path
        else:
            raise RuntimeError(f"Failed to fetch file: {got_path.resolve()}")


def drop(dataset_path: Path) -> None:
    """Drop and remove junifer-data dataset at ``dataset_path``.

    Parameters
    ----------
    dataset_path : pathlib.Path
        Path to the dataset.

    Raises
    ------
    RuntimeError
        If there is a problem cleaning the dataset.

    """
    try:
        dl.drop(
            dataset_path,
            what="all",
            reckless="kill",
            dataset=dataset_path,
            recursive=True,
        )
    except (CommandError, NoDatasetFound) as e:
        raise RuntimeError(f"Failed to drop dataset: {e}") from e
    else:
        logger.debug(f"Successfully dropped dataset: {dataset_path}")
