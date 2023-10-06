import contextlib
import shutil
import tempfile
from pathlib import Path

from edne_correios_loader.table_set import TableSetEnum, get_table_files_glob
from edne_correios_loader.resolver import DELIMITED_SUBDIR

TEST_DNE_DIR = Path(Path("tests/data/dne").absolute())


class CreateTemporaryDneDirectory:
    def __enter__(self):
        self.outerdir = tempfile.mkdtemp()

        self.innerdir = Path(self.outerdir) / DELIMITED_SUBDIR
        self.innerdir.mkdir()
        self.create_files()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.outerdir)

    def create_files(self):
        for table in TableSetEnum.ALL_TABLES.to_populate:
            glob = get_table_files_glob(table)

            if glob is None:
                continue

            if glob == "LOG_LOGRADOURO_*.TXT":
                files = [glob.replace("*", "SP"), glob.replace("*", "BA")]
            else:
                files = [glob]

            for file in files:
                (self.innerdir / file).touch()

    def populate_file(self, file, rows):
        rows = ["@".join(field or "" for field in line) for line in rows]
        with (self.innerdir / file).open("w", encoding="latin-1") as f:
            f.write("\n".join(rows))


@contextlib.contextmanager
def create_inner_dne_zip_file() -> str:
    with CreateTemporaryDneDirectory() as dne_dir:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield shutil.make_archive(
                str(Path(tmpdir) / "dne"),
                "zip",
                root_dir=dne_dir.outerdir,
                base_dir="delimitado",
            )
