import logging
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Union
from urllib.parse import urlparse

from .exc import DneResolverError
from .table_set import TableSetEnum, get_table_files_glob

if TYPE_CHECKING:
    from zipfile import ZipFile

logger = logging.getLogger(__name__)

DELIMITED_SUBDIR = "Delimitado"


LATEST_DNE_DOWNLOAD_URL = (
    "https://www2.correios.com.br/sistemas/edne/download/eDNE_Basico.zip"
)


class DneResolver:
    """
    Resolves the DNE source path.

    The provided dne_source string can be:
        - None: Then the latest DNE will be downloaded from Correios website
        - A ZIP file URL: Then the DNE will be downloaded and extracted
        - A local ZIP file: Then the file will be extracted
        - A local folder: Then the folder will be validated and used as the DNE source

    Returns the path to the resolved DNE folder.
    """

    dne_source: Union[str, None]

    def __init__(self, dne_source: Union[str, None] = None):
        self.dne_source = dne_source

        # keep track of temporary files to be removed
        self.temp_artifacts = []

    def __enter__(self):
        try:
            logger.info("Resolving DNE source...", extra={"indentation": 0})
            return self.resolve_dne_source(self.dne_source)
        except Exception:
            self.remove_temp_artifacts()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val and self.temp_artifacts:
            logger.warning(
                "Something went wrong. Removing temporary files...",
                extra={"indentation": 0},
            )
        self.remove_temp_artifacts()

    def resolve_dne_source(self, dne_source: str):
        if dne_source is None:
            logger.info(
                "No DNE source provided, the latest DNE will be downloaded from "
                "Correios website",
                extra={"indentation": 0},
            )
            dne_source = LATEST_DNE_DOWNLOAD_URL

        # if the provided source looks like a URL, download it
        if looks_like_a_url(dne_source):
            logger.debug("Source identified as URL")
            dne_source = self.download_dne(dne_source)

            logger.debug('DNE downloaded to "%s"', dne_source)

        # if the provided source is a file, try to unzip it
        if Path(dne_source).is_file():
            dne_source = self.resolve_file_source(dne_source)
            # remove no more needed temp files/dirs
            self.remove_temp_artifacts(keep_last=True)

        if (dne_dir := Path(dne_source)).is_dir():
            return self.resolve_dir_source(dne_dir)

        msg = f"DNE source not found: {dne_source}"
        raise DneResolverError(msg)

    def resolve_file_source(self, dne_source: str):
        try:
            with zipfile.ZipFile(dne_source, mode="r") as archive:
                logger.debug("Source identified as ZIP file: %s", dne_source)
                # At this point we know it's a ZIP file, but it can be one of:
                # 1. A ZIP file downloaded from Correios website containing two ZIP
                # files:
                #    - eDNE_Basico_YYMM.zip
                #    - eDNE_Delta_Basico_YYMM.zip
                # 2. The eDNE_Basico_YYMM.zip file extracted from the ZIP file above

                if dne_basico_filename := zip_contains_dne_basico_zip_file(archive):
                    logger.debug(
                        "Source is as ZIP file containing a DNE Basico ZIP file"
                    )
                    # if the ZIP file contains a DNE Basico ZIP file, extract it
                    temp_dir = tempfile.mkdtemp()
                    self.temp_artifacts.append(temp_dir)

                    logger.debug(
                        'Extracting "%s" to "%s"',
                        dne_basico_filename,
                        temp_dir,
                    )
                    extracted_zip = archive.extract(dne_basico_filename, temp_dir)

                    # start the resolver again with the extracted ZIP file as source
                    return self.resolve_dne_source(extracted_zip)

                # the ZIP file isn't a ZIP file containing other ZIP files,
                # so let's check if it's a DNE Basico ZIP file

                valid_dne_files = [
                    f for f in archive.namelist() if filename_is_a_dne_basico_file(f)
                ]

                if valid_dne_files:
                    temp_dir = tempfile.mkdtemp()
                    self.temp_artifacts.append(temp_dir)

                    logger.debug(
                        "Source is a DNE Basico ZIP file, extracting %s files to %s",
                        len(valid_dne_files),
                        temp_dir,
                    )

                    for file in valid_dne_files:
                        archive.extract(file, temp_dir)

                    return temp_dir

                msg = "ZIP file does not contain DNE Basico files"
                raise DneResolverError(msg)

        except zipfile.BadZipFile as e:
            msg = f"Source is not a valid ZIP file: {dne_source}"
            raise DneResolverError(msg) from e

    def resolve_dir_source(self, dne_dir: Path):
        # assert all the data files are present
        for table in TableSetEnum.ALL_TABLES.to_populate:
            # check if there are source files for all tables to be created
            if (file_glob := get_table_files_glob(table)) and not any(
                dne_dir.glob(file_glob)
            ):
                if (delimited_subdir := (dne_dir / DELIMITED_SUBDIR)).is_dir():
                    return self.resolve_dne_source(str(delimited_subdir))

                msg = f"DNE data file not found: {dne_dir / file_glob}"
                raise DneResolverError(msg)

        return dne_dir

    def download_dne(self, url: str) -> str:
        """
        Download zipped DNE and returns the path to the downloaded file.
        """
        bs = 1024 * 8

        try:
            with urllib.request.urlopen(url) as response:  # noqa: S310
                total_size = int(response.headers.get("Content-Length", -1))
                self.download_report_hook(0, total_size, "start")

                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    # add downloaded file to the list of files to be removed
                    self.temp_artifacts.append(tmp_file.name)

                    while block := response.read(bs):
                        tmp_file.write(block)
                        self.download_report_hook(len(block), total_size, "progress")

                    self.download_report_hook(0, total_size, "finish")

        except urllib.error.URLError as e:
            msg = f"Failed to download DNE from {url}"
            raise DneResolverError(msg) from e

        return tmp_file.name

    def download_report_hook(self, read: int, total: int, hook_type: str):
        pass

    def remove_temp_artifacts(self, *, keep_last: bool = False):
        """
        Remove all temporary files created by the resolver.
        """

        while num_artifacts := len(self.temp_artifacts):
            if num_artifacts < 2 and keep_last:  # noqa: PLR2004
                return

            to_remove = self.temp_artifacts.pop(0)

            if Path(to_remove).is_file():
                logger.debug("Removing temporary file %s", to_remove)
                Path(to_remove).unlink()
            else:
                logger.debug("Removing temporary directory %s", to_remove)
                shutil.rmtree(to_remove)


def looks_like_a_url(url):
    """
    Rudimentar check to see if a string looks like a URL.
    """
    result = urlparse(url)
    return all([result.scheme, result.netloc, result.scheme in ("http", "https")])


def zip_contains_dne_basico_zip_file(zipfile: "ZipFile") -> Union[str, None]:
    """
    Check if the provided ZIP file contains a DNE Basico ZIP file.
    If true, returns the path to the DNE Basico ZIP file.
    """
    for filename in zipfile.namelist():
        lowered_name = filename.lower()
        if lowered_name.startswith("edne_basico_") and lowered_name.endswith(".zip"):
            return filename

    return None


def filename_is_a_dne_basico_file(filename: str) -> bool:
    """
    Check if the provided filename is part of a DNE Basico package.
    """
    name = filename.lower()
    return name == "leiame.txt" or (
        name.startswith(f"{DELIMITED_SUBDIR.lower()}/") and name.endswith(".txt")
    )


# def extract_dne_version(dne_path: Path) -> int:
#     """
#     Extracts the DNE version from the provided path
#     by reading it from the LEIAME.TXT file
#     """
#     leiame_file = dne_path / Path("LEIAME.TXT")
#
#     if not leiame_file.is_file():
#         msg = f"Failed to extract DNE version. File not found: {leiame_file}"
#         raise DneResolverError(msg)
#
#     content = leiame_file.open(encoding="latin1").read()
#     match = re.compile(r"DNE versão (?P<version>\d{5})").search(content)
#
#     if not match:
#         msg = f"Failed to extract DNE version. Version not found in {leiame_file}"
#         raise DneResolverError(msg)
#
#     return int(match.group("version"))
