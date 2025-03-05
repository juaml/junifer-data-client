"""Tests for junifer_data.utils."""

from pathlib import Path

import pytest

from junifer_data import check_dataset


def test_check_dataset_main(tmp_path: Path) -> None:
    """Test check_dataset with main tag.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    dataset = check_dataset(data_dir=tmp_path)
    assert dataset.pathobj.name == "main"


def test_check_dataset_hexsha_errors(tmp_path: Path) -> None:
    """Test check_dataset hexsha errors.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    with pytest.raises(ValueError, match="Cannot verify hexsha for main tag."):
        check_dataset(data_dir=tmp_path, hexsha="wrong")

    with pytest.raises(ValueError, match="Commit verification failed."):
        check_dataset(data_dir=tmp_path, tag="1", hexsha="wrong")

    # Now clone the dataset without checking
    check_dataset(data_dir=tmp_path, tag="1")

    with pytest.raises(ValueError, match="Commit verification failed."):
        check_dataset(data_dir=tmp_path, tag="1", hexsha="wrong")

    # Check with the right hexsha
    check_dataset(
        data_dir=tmp_path,
        tag="1",
        hexsha="e9aecf7b5a2fff82de00d265e02afde42a448647",
    )

    ds_path = tmp_path / "v1"

    with open(ds_path / "test.txt", "w") as f:
        f.write("test")

    with pytest.raises(RuntimeError, match="dirty junifer-data"):
        check_dataset(data_dir=tmp_path, tag="1")
