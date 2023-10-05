import contextlib
import io
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock
from zipfile import ZipFile

import pytest

from dne_correios_loader.exc import DneResolverError
from dne_correios_loader.resolver import LATEST_DNE_DOWNLOAD_URL, DneResolver

from .shared import TEST_DNE_DIR, create_inner_dne_zip_file


def has_a_dne_file(path: Path):
    return (path / "LOG_LOCALIDADE.TXT").is_file()


@pytest.fixture
def temp_zip_file():
    file = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    try:
        yield ZipFile(file, "w")
    finally:
        file.close()
        Path(file.name).unlink(missing_ok=True)


@pytest.fixture
def inner_dne_zip_path() -> str:
    with create_inner_dne_zip_file() as path:
        yield path


@pytest.fixture
def inner_dne_zip_content(inner_dne_zip_path) -> bytes:
    return Path(inner_dne_zip_path).read_bytes()


@pytest.fixture
def outer_dne_zip_path(inner_dne_zip_path) -> str:
    file = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    try:
        with ZipFile(file, "w") as zf:
            zf.write(inner_dne_zip_path, "eDNE_Basico_23091.zip")

        yield file.name

    finally:
        file.close()
        Path(file.name).unlink(missing_ok=True)


@pytest.fixture
def outer_dne_zip_content(outer_dne_zip_path) -> bytes:
    return Path(outer_dne_zip_path).read_bytes()


@pytest.fixture
def corrupted_zip_file() -> str:
    file = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    file.write(b"corrupted-zip-file-or-some-other-content")
    file.close()

    try:
        yield file.name
    finally:
        Path(file.name).unlink(missing_ok=True)


@pytest.fixture
def assert_temp_artifacts_are_removed():
    @contextlib.contextmanager
    def assert_temp_artifacts_are_removed_func(url):
        with mock.patch.object(
            DneResolver, "remove_temp_artifacts", autospec=True
        ) as remove_temp_artifacts:
            resolver = DneResolver(url)
            yield resolver

        # assert the function was called
        remove_temp_artifacts.assert_called()

        temp_artifacts = resolver.temp_artifacts[:]
        # assert the temp files are still there
        assert all(Path(p).exists() for p in temp_artifacts)

        # run for real
        resolver.remove_temp_artifacts()
        # assert it removed all temp artifacts
        assert all(not Path(p).exists() for p in temp_artifacts)

    return assert_temp_artifacts_are_removed_func


# source is rubbish


def test_resolver_raises_when_source_is_invalid_path():
    with pytest.raises(DneResolverError) as e, DneResolver("invalid-path"):
        pass  # pragma: no cover

    e.match("DNE source not found")


# source is a directory


def test_resolver_raises_when_source_is_a_directory_without_dne_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(DneResolverError) as e, DneResolver(temp_dir):
            pass  # pragma: no cover

        e.match("DNE data file not found")


def test_resolver_raises_when_source_is_a_directory_missing_any_dne_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        Path(temp_dir, "LOG_BAIRRO.TXT").touch()
        Path(temp_dir, "ECT_PAIS.TXT").touch()

        with pytest.raises(DneResolverError) as e, DneResolver(temp_dir):
            pass  # pragma: no cover

        e.match("DNE data file not found")


# @pytest.mark.parametrize(
#     "input_dir, resolved_dir",
#     (
#         [str(TEST_DNE_DIR), TEST_DNE_DIR / "Delimitado"],
#         [str(TEST_DNE_DIR / "delimitado"), TEST_DNE_DIR / "delimitado"],
#     ),
# )
def test_resolver_returns_path_when_source_is_valid_dne_directory(temporary_dne_dir):
    with DneResolver(str(temporary_dne_dir.outerdir)) as dne_dir:
        assert has_a_dne_file(dne_dir)
        assert dne_dir == temporary_dne_dir.innerdir

    with DneResolver(str(temporary_dne_dir.innerdir)) as dne_dir:
        assert has_a_dne_file(dne_dir)
        assert dne_dir == temporary_dne_dir.innerdir


# source is a ZIP file


def test_resolver_raises_when_source_is_an_invalid_zip_file(corrupted_zip_file):
    """
    Or not a ZIP file at all
    """
    with pytest.raises(DneResolverError) as e, DneResolver(corrupted_zip_file):
        pass  # pragma: no cover

    e.match("Source is not a valid ZIP file")


def test_resolver_raises_when_source_is_a_zip_file_without_dne_files(temp_zip_file):
    with temp_zip_file:
        temp_zip_file.writestr("some-random-file.txt", "file-content")

    with pytest.raises(DneResolverError) as e, DneResolver(temp_zip_file.filename):
        pass  # pragma: no cover

    e.match("ZIP file does not contain DNE Basico files")


def test_resolver_raises_when_source_is_a_zip_file_missing_any_dne_file(temp_zip_file):
    with temp_zip_file:
        temp_zip_file.writestr("delimitado/LOG_BAIRRO.TXT", "file-content")
        temp_zip_file.writestr("delimitado/ECT_PAIS.TXT", "file-content")

    with pytest.raises(DneResolverError) as e, DneResolver(temp_zip_file.filename):
        pass  # pragma: no cover

    e.match("DNE data file not found")


def test_resolver_returns_path_when_source_is_a_valid_dne_zip_file(inner_dne_zip_path):
    """
    eDNE_Basico_23091.zip -> FILES
    """
    with DneResolver(inner_dne_zip_path) as dne_dir:
        assert has_a_dne_file(dne_dir)


def test_resolver_returns_path_when_source_is_a_valid_dne_zip_file_inside_another_zip(
    outer_dne_zip_path,
):
    """
    eDNE_Basico.zip -> eDNE_Basico_23091.zip -> FILES
    """
    with DneResolver(outer_dne_zip_path) as dne_dir:
        assert has_a_dne_file(dne_dir)


# source is a URL


def test_resolver_raises_when_source_is_an_invalid_url(mock_urlopen):
    with mock_urlopen(urllib.error.URLError("Invalid URL")) as url:
        with pytest.raises(DneResolverError) as e, DneResolver(url):
            pass  # pragma: no cover

        e.match("Failed to download DNE")

    with mock_urlopen(
        urllib.error.HTTPError(
            "http://non-existing-url", 404, "Not Found", {}, io.BytesIO()
        )
    ) as url:
        with pytest.raises(DneResolverError) as e, DneResolver(url):
            pass  # pragma: no cover

        e.match("Failed to download DNE")


def test_resolver_raises_when_source_is_url_with_non_zip_file(mock_urlopen):
    with mock_urlopen(b"corrupted-zip-file-or-some-other-content") as url:
        with pytest.raises(DneResolverError) as e, DneResolver(url):
            pass  # pragma: no cover

    e.match("Source is not a valid ZIP file")


def test_resolver_raises_when_source_is_url_with_zip_with_invalid_content(
    mock_urlopen, temp_zip_file
):
    with temp_zip_file:
        temp_zip_file.writestr("some-random-file.txt", "file-content")

    zip_content = Path(temp_zip_file.filename).read_bytes()

    with mock_urlopen(zip_content) as url:
        with pytest.raises(DneResolverError) as e, DneResolver(url):
            pass  # pragma: no cover

    e.match("ZIP file does not contain DNE Basico files")


def test_resolver_raises_when_source_is_zip_missing_some_dne_files(
    mock_urlopen, temp_zip_file
):
    with temp_zip_file:
        temp_zip_file.writestr("delimitado/LOG_BAIRRO.TXT", "file-content")
        temp_zip_file.writestr("delimitado/ECT_PAIS.TXT", "file-content")

    zip_content = Path(temp_zip_file.filename).read_bytes()

    with mock_urlopen(zip_content) as url:
        with pytest.raises(DneResolverError) as e, DneResolver(url):
            pass  # pragma: no cover

    e.match("DNE data file not found")


def test_resolver_returns_path_when_source_is_url_with_valid_dne(
    mock_urlopen, outer_dne_zip_content, inner_dne_zip_content
):
    """
    Testing both cases:
    - URL -> eDNE_Basico.zip -> eDNE_Basico_23091.zip -> FILES
    - URL -> eDNE_Basico_23091.zip -> FILES
    """
    with mock_urlopen(outer_dne_zip_content) as url:
        with DneResolver(url) as dne_dir:
            assert has_a_dne_file(dne_dir)

    with mock_urlopen(inner_dne_zip_content) as url:
        with DneResolver(url) as dne_dir:
            assert has_a_dne_file(dne_dir)


def test_resolver_downloads_dne_from_correios_when_source_is_not_defined(
    outer_dne_zip_content, mock_urlopen
):
    with mock_urlopen(outer_dne_zip_content, url=LATEST_DNE_DOWNLOAD_URL):
        with DneResolver() as dne_dir:
            assert has_a_dne_file(dne_dir)


def test_resolver_removes_temporary_artifacts_after_resolving_url(
    outer_dne_zip_content, mock_urlopen, assert_temp_artifacts_are_removed
):
    with mock_urlopen(outer_dne_zip_content) as url:
        with assert_temp_artifacts_are_removed(url) as resolver:
            with resolver as dne_dir:
                assert has_a_dne_file(dne_dir)

            # zip, extracted outer zip, extracted inner zip
            assert len(resolver.temp_artifacts) == 3


def test_resolver_removes_temporary_artifacts_if_errors_out_resolving_the_source(
    mock_urlopen, temp_zip_file, assert_temp_artifacts_are_removed
):
    with temp_zip_file:
        temp_zip_file.writestr("some-random-file.txt", "file-content")

    temp_zip_content = Path(temp_zip_file.filename).read_bytes()

    with mock_urlopen(temp_zip_content) as url:
        with assert_temp_artifacts_are_removed(url) as resolver:
            with pytest.raises(DneResolverError), resolver:
                pass  # pragma: no cover

            assert len(resolver.temp_artifacts) > 0


def test_resolver_removes_temporary_artifacts_if_inner_code_errors_out(
    mock_urlopen, inner_dne_zip_content, assert_temp_artifacts_are_removed
):
    with mock_urlopen(inner_dne_zip_content) as url:
        with assert_temp_artifacts_are_removed(url) as resolver:
            with pytest.raises(ValueError), resolver:
                msg = "Some unexpected error here"
                raise ValueError(msg)

            # zip, extracted inner zip
            assert len(resolver.temp_artifacts) == 2
