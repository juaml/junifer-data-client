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


def test_get_fetches_directories(tmp_path: Path, check_calls: list) -> None:
    """Test get fetches directory contents even if the directory exists.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.
    check_calls : list of dict
        The calls to check_dataset.

    """
    dir_path = Path("parcellations/AICHA/v1")
    file_path = tmp_path / "v1" / dir_path / "AICHAmc.nii.lut"
    get(dir_path, dataset_path=tmp_path, tag="1")
    # Annexed file content is present
    assert file_path.is_file()


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


def test_has_content(tmp_path: Path) -> None:
    """Test files only have content when it is not an annex pointer.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    content = tmp_path / "content.txt"
    content.write_text("some content")
    assert _functions._has_content(content)
    # Unlocked file without its content
    pointer = tmp_path / "pointer.nii.gz"
    pointer.write_text("/annex/objects/MD5E-s361253--7d0629e04eca7.nii.gz\n")
    assert not _functions._has_content(pointer)
    # Locked file without its content
    broken = tmp_path / "broken.nii.gz"
    broken.symlink_to(tmp_path / "missing")
    assert not _functions._has_content(broken)
    # Locked file with its content
    locked = tmp_path / "locked.txt"
    locked.symlink_to(content)
    assert _functions._has_content(locked)
    # Directories go through datalad get
    assert not _functions._has_content(tmp_path)


def test_annex_pointer_format(tmp_path: Path) -> None:
    """Test git-annex pointer files are detected as without content.

    Checks the format of the pointer files git-annex creates for unlocked
    files without content, which ``_has_content`` relies on.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    # Dataset with an unlocked annexed file
    source = dl.create(tmp_path / "source", result_renderer="disabled")
    source.repo.config.set("annex.addunlocked", "true", scope="local")
    (source.pathobj / "data.bin").write_bytes(b"\x00binary content")
    source.save(result_renderer="disabled")
    # A clone has the pointer file until the content is fetched
    clone = dl.clone(
        source=source.path,
        path=tmp_path / "clone",
        result_renderer="disabled",
    )
    pointer = clone.pathobj / "data.bin"
    assert pointer.read_bytes().startswith(_functions._ANNEX_POINTER_PREFIX)
    assert not _functions._has_content(pointer)
    clone.get("data.bin", result_renderer="disabled")
    assert pointer.read_bytes() == b"\x00binary content"
    assert _functions._has_content(pointer)


def test_get_unlocked_file(tmp_path: Path) -> None:
    """Test get fetches the content of unlocked files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture that provides a temporary directory.

    """
    # Unlocked file, so a pointer file until its content is fetched
    file_path = Path(
        "parcellations/Schaefer2018/Yeo2011/"
        "Schaefer2018_1000Parcels_17Networks_order_FSLMNI152_1mm.nii.gz"
    )
    fetched = get(file_path, dataset_path=tmp_path, tag="8")
    # Gzip magic number
    assert fetched.read_bytes()[:2] == b"\x1f\x8b"
