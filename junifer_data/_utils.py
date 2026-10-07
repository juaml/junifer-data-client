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


JUNIFER_DATA_URL = "https://cerebra.fz-juelich.de/junifer/junifer-data.git"

# Previous locations of junifer-data, used to migrate existing installations
_OLD_JUNIFER_DATA_URLS = (
    "https://github.com/juaml/junifer-data",
    "https://github.com/juaml/junifer-data.git",
    "git@github.com:juaml/junifer-data.git",
    "ssh://git@github.com/juaml/junifer-data.git",
)

# Retired GIN location, removed from existing installations
_GIN_JUNIFER_DATA_URLS = (
    "https://gin.g-node.org/synchon/junifer-data",
    "https://gin.g-node.org/synchon/junifer-data.git",
)


def _migrate_origin(dataset: dl.Dataset) -> None:
    """Point the ``origin`` remote of an old installation to the new URL.

    Only ``origin`` is touched and only if it points to a known old
    location; user-configured remotes are preserved.

    Parameters
    ----------
    dataset : datalad.api.Dataset
        The junifer-data dataset.

    """
    repo = dataset.repo
    origin_url = repo.config.get("remote.origin.url")
    if origin_url not in _OLD_JUNIFER_DATA_URLS:
        return
    logger.info(
        f"Migrating junifer-data remote from {origin_url} to "
        f"{JUNIFER_DATA_URL}"
    )
    repo.call_git(["remote", "set-url", "origin", JUNIFER_DATA_URL])
    # GitHub cannot host annexed content, so git-annex marks it as ignored;
    # drop the cached annex settings so the new remote gets probed again
    for key in ("annex-ignore", "annex-uuid"):
        if f"remote.origin.{key}" in repo.config:
            repo.config.unset(
                f"remote.origin.{key}", scope="local", reload=False
            )
    repo.config.reload(force=True)


def _remove_gin_remotes(dataset: dl.Dataset) -> None:
    """Remove remotes pointing to the retired GIN location.

    Installations made before GIN was retired have it auto-enabled, and
    tagged installations never fetch the git-annex branch that marks it as
    dead. Only remotes pointing to a known GIN location are removed;
    user-configured remotes are preserved.

    Parameters
    ----------
    dataset : datalad.api.Dataset
        The junifer-data dataset.

    """
    repo = dataset.repo
    for remote in repo.get_remotes():
        url = repo.config.get(f"remote.{remote}.url")
        if url in _GIN_JUNIFER_DATA_URLS:
            logger.info(f"Removing retired junifer-data remote: {url}")
            repo.remove_remote(remote)


def check_dataset(
    data_dir: Union[str, Path, None] = None,
    tag: Optional[str] = None,
    hexsha: Optional[str] = None,
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
    hexsha: str or None, optional
        Commit hash to verify. If None, no verification will be performed.

    Returns
    -------
    datalad.api.Dataset
        The junifer-data dataset.

    Raises
    ------
    RuntimeError
        If there is a problem checking the dataset.
    ValueError
        If ``hexsha`` is provided for the main tag or
        if unknown tag is provided or
        if ``hexsha`` is provided but does not match the checked out ``tag``.

    """
    # Check tag
    if tag is not None:
        tag = f"v{tag}"
    else:
        tag = "main"

    # Avoid hexsha check for main
    if tag == "main" and hexsha is not None:
        raise ValueError("Cannot verify hexsha for main tag.")

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
        # Check if dataset is dirty
        if dataset.repo.dirty:
            raise RuntimeError(
                f"Found dirty junifer-data at: {data_dir.resolve()} . "
                "You can clean or delete the directory."
            )
        _migrate_origin(dataset)
        _remove_gin_remotes(dataset)
        if tag == "main":
            # Main tag, use the latest commit
            try:
                dataset.update()
            except CommandError as e:
                raise RuntimeError(
                    f"Failed to update junifer-data: {e}"
                ) from e
            else:
                logger.debug("Successfully updated junifer-data")
        else:
            # Get commit hash for the tag
            tag_hexsha = [
                x["hexsha"]
                for x in dataset.repo.get_tags()
                if x["name"] == tag
            ]
            # Check for incorrect tags
            if not tag_hexsha:
                raise ValueError(f"Unknown tag: {tag} for junifer-data.")

            # Get commit hash for HEAD
            head_hexsha = dataset.repo.get_hexsha()
            # Get tag hexsha
            tag_hexsha = tag_hexsha[0]
            # Check that it matches the expected hexsha from the tag info
            if head_hexsha != tag_hexsha:
                raise ValueError(
                    f"Wrong commit checked out for tag: {tag}. "
                    f"Expected: {tag_hexsha}, got: {head_hexsha}."
                )

            # Do hexsha verification for other tags if provided
            # Check that the hexsha matches the expected hexsha from the user
            # head_hexsha is now verified and can be used for checking
            if hexsha is not None and head_hexsha != hexsha:
                raise ValueError(
                    f"Commit verification failed for tag: {tag}. "
                    f"Expected: {head_hexsha}, got: {hexsha}."
                )
    else:
        logger.debug(f"Cloning junifer-data to: {data_dir.resolve()}")
        # Clone dataset
        try:
            dataset = dl.clone(
                JUNIFER_DATA_URL,
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
        _remove_gin_remotes(dataset)
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
