"""Tests for junifer_data.functions."""

from pathlib import Path

import datalad.api as dl
import pytest

from junifer_data import _functions, check_dataset, get


@pytest.fixture
def check_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Record the calls to check_dataset made by get.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture to patch objects.

    Returns
    -------
    list of dict
        The keyword arguments of each call.

    """
    calls = []

    def recording_check_dataset(**kwargs):
        calls.append(kwargs)
        return check_dataset(**kwargs)

    monkeypatch.setattr(_functions, "check_dataset", recording_check_dataset)
    monkeypatch.setattr(_functions, "_checked_datasets", {})
    return calls


def test_get_checks_dataset_once(tmp_path: Path, check_calls: list) -> None:
    """Test get checks a tagged dataset only once.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.
    check_calls : list of dict
        The calls to check_dataset.

    """
    first = get(
        Path("coordinates/CogAR/CogAR_VOIs.txt"),
        dataset_path=tmp_path,
        tag="1",
    )
    second = get(
        Path("coordinates/CogAC/CogAC_VOIs.txt"),
        dataset_path=tmp_path,
        tag="1",
    )
    assert first.exists()
    assert second.exists()
    assert len(check_calls) == 1


def test_get_checks_main_every_time(tmp_path: Path, check_calls: list) -> None:
    """Test get checks (and updates) the main tag on every call.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.
    check_calls : list of dict
        The calls to check_dataset.

    """
    for _ in range(2):
        get(Path("coordinates/CogAR/CogAR_VOIs.txt"), dataset_path=tmp_path)
    assert len(check_calls) == 2


def test_get_skips_present_files(
    tmp_path: Path, check_calls: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test get does not call datalad get for files already present.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.
    check_calls : list of dict
        The calls to check_dataset.
    monkeypatch : pytest.MonkeyPatch
        Pytest fixture to patch objects.

    """
    # Annexed file, so its content is fetched by the first call
    file_path = Path("parcellations/AICHA/v1/AICHAmc.nii.lut")
    fetched = get(file_path, dataset_path=tmp_path, tag="1")
    assert fetched.exists()

    def fail_get(*args, **kwargs):
        pytest.fail("datalad get should not be called")

    monkeypatch.setattr(dl.Dataset, "get", fail_get)
    again = get(file_path, dataset_path=tmp_path, tag="1")
    assert again.resolve() == fetched.resolve()


def test_get_checks_removed_dataset(tmp_path: Path, check_calls: list) -> None:
    """Test get checks the dataset again if it was removed.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.
    check_calls : list of dict
        The calls to check_dataset.

    """
    file_path = Path("coordinates/CogAR/CogAR_VOIs.txt")
    get(file_path, dataset_path=tmp_path, tag="1")
    dl.Dataset(tmp_path / "v1").remove(
        reckless="kill", result_renderer="disabled"
    )
    assert get(file_path, dataset_path=tmp_path, tag="1").exists()
    assert len(check_calls) == 2
