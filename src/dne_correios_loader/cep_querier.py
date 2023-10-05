from typing import Union

from sqlalchemy import create_engine

from .tables import metadata


class CepQuerier:
    cep_table = metadata.tables["cep_unificado"]

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)

    def query(self, cep: str) -> Union[dict, None]:
        cep = cep.replace("-", "").strip()

        with self.engine.connect() as conn:
            cep = conn.execute(
                self.cep_table.select().where(self.cep_table.c.cep == cep)
            ).first()

            return cep._asdict() if cep else None
