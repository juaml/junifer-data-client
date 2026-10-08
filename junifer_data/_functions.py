"""Functions for junifer-data."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import datalad.api as dl
from datalad.runner.exception import CommandError
from datalad.support.exceptions import IncompleteResultsError, NoDatasetFound

from ._utils import check_dataset


__all__ = ["drop", "get"]


logger = logging.getLogger(__name__)

# Start of the pointer files of unlocked annexed files without content
_ANNEX_POINTER_PREFIX = b"/annex/objects/"

# Datasets already checked in this process, by (location, tag, hexsha)
_checked_datasets: dict[tuple, dl.Dataset] = {}


def _has_content(path: Path) -> bool:
    """Check whether an annexed file has its content.

    Locked files are symlinks to the content, so they only exist once the
    content is present. Unlocked files are pointer files (with the path to
    the annexed object) until the content is present.

    Parameters
    ----------
    path : pathlib.Path
        The path to the file.

    Returns
    -------
    bool
        Whether the file exists and has its content.

    """
    if not path.is_file():
        return False
    with path.open("rb") as f:
        return f.read(len(_ANNEX_POINTER_PREFIX)) != _ANNEX_POINTER_PREFIX


def _get_checked_dataset(
    dataset_path: Path | None,
    tag: str | None,
    hexsha: str | None,
) -> dl.Dataset:
    """Get the dataset, checking it only once per process.

    Checking the dataset runs several git commands, which is slow when
    fetching many files. The ``main`` tag is always checked, as it is
    updated on every check.

    Parameters
    ----------
    dataset_path : pathlib.Path or None
        Path to the dataset.
    tag : str or None
        Tag to checkout.
    hexsha : str or None
        Commit hash to verify.

    Returns
    -------
    datalad.api.Dataset
        The junifer-data dataset.

    """
    key = (
        None if dataset_path is None else str(Path(dataset_path).resolve()),
        tag,
        hexsha,
    )
    dataset = _checked_datasets.get(key)
    # Check again if the dataset was removed in the meantime
    if dataset is None or not dataset.is_installed():
        dataset = check_dataset(data_dir=dataset_path, tag=tag, hexsha=hexsha)
        if tag is not None:
            _checked_datasets[key] = dataset
    return dataset


def get(
    file_path: Path,
    dataset_path: Path | None = None,
    tag: str | None = None,
    hexsha: str | None = None,
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
    dataset = _get_checked_dataset(
        dataset_path=dataset_path, tag=tag, hexsha=hexsha
    )
    # Skip the (slow) datalad get if the file already has its content;
    # directories always go through datalad get
    local_path = dataset.pathobj / file_path
    if _has_content(local_path):
        logger.debug(f"Found existing file: {local_path.resolve()}")
        return local_path
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
