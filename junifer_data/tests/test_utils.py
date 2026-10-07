"""Tests for junifer_data.utils."""

from pathlib import Path

import datalad.api as dl
import pytest

from junifer_data import check_dataset
from junifer_data._utils import JUNIFER_DATA_URL


def test_check_dataset_main(tmp_path: Path) -> None:
    """Test check_dataset with main tag.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    dataset = check_dataset(data_dir=tmp_path)
    assert dataset.pathobj.name == "main"

    # Check-out again, should update
    check_dataset(data_dir=tmp_path)


def test_check_dataset_tag_errors(tmp_path: Path) -> None:
    """Test check_dataset hexsha errors.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    with pytest.raises(RuntimeError, match="Failed to checkout state"):
        check_dataset(data_dir=tmp_path, tag="wrong")


def test_check_dataset_hexsha_errors(tmp_path: Path) -> None:
    """Test check_dataset hexsha errors.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    with pytest.raises(
        ValueError, match=r"Cannot verify hexsha for main tag."
    ):
        check_dataset(data_dir=tmp_path, hexsha="wrong")

    # Now clone the dataset without checking
    check_dataset(data_dir=tmp_path, tag="1")

    with pytest.raises(ValueError, match=r"Commit verification failed."):
        check_dataset(data_dir=tmp_path, tag="1", hexsha="wrong")

    # Check with the right hexsha
    dataset = check_dataset(
        data_dir=tmp_path,
        tag="1",
        hexsha="e9aecf7b5a2fff82de00d265e02afde42a448647",
    )

    ds_path = tmp_path / "v1"

    with open(ds_path / "test.txt", "w") as f:
        f.write("test")

    with pytest.raises(RuntimeError, match="dirty junifer-data"):
        check_dataset(data_dir=tmp_path, tag="1")

    # We will now update the tag
    dataset.repo.add((ds_path / "test.txt").as_posix())
    dataset.repo.commit(msg="update")

    with pytest.raises(ValueError, match=r"Wrong commit checked out."):
        check_dataset(data_dir=tmp_path, tag="1")

    # Update tag
    dataset.repo.tag("v1", options=["-d"])
    dataset.repo.tag("v1")

    # Does not fail
    check_dataset(data_dir=tmp_path, tag="1")

    # But does not have the right hexsha
    with pytest.raises(ValueError, match=r"Commit verification failed."):
        check_dataset(
            data_dir=tmp_path,
            tag="1",
            hexsha="e9aecf7b5a2fff82de00d265e02afde42a448647",
        )


def test_check_dataset_migrates_old_origin(tmp_path: Path) -> None:
    """Test check_dataset migrates an installation cloned from GitHub.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    dataset = check_dataset(data_dir=tmp_path)
    repo = dataset.repo
    # Simulate an installation cloned from GitHub
    repo.call_git(
        [
            "remote",
            "set-url",
            "origin",
            "https://github.com/juaml/junifer-data.git",
        ]
    )
    repo.config.unset("remote.origin.annex-uuid", scope="local")
    repo.config.set("remote.origin.annex-ignore", "true", scope="local")
    # Add a user-configured remote, which should be preserved
    mine = tmp_path / "mine"
    dl.create(mine, annex=False, result_renderer="disabled")
    repo.call_git(["remote", "add", "mine", mine.as_posix()])

    dataset = check_dataset(data_dir=tmp_path)
    config = dataset.repo.config
    config.reload(force=True)
    assert config.get("remote.origin.url") == JUNIFER_DATA_URL
    assert "remote.origin.annex-ignore" not in config
    assert config.get("remote.mine.url") == mine.as_posix()


def test_check_dataset_removes_gin(tmp_path: Path) -> None:
    """Test check_dataset removes the retired GIN remote.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    dataset = check_dataset(data_dir=tmp_path, tag="7")
    repo = dataset.repo
    assert "gin-data" not in repo.get_remotes()

    # Simulate a tagged installation made while GIN was auto-enabled
    repo.add_remote("gin-data", "https://gin.g-node.org/synchon/junifer-data")
    # Add a user-configured remote, which should be preserved
    mine = tmp_path / "mine"
    dl.create(mine, annex=False, result_renderer="disabled")
    repo.add_remote("mine", mine.as_posix())

    dataset = check_dataset(data_dir=tmp_path, tag="7")
    remotes = dataset.repo.get_remotes()
    assert "gin-data" not in remotes
    assert "mine" in remotes
