from sqlalchemy import create_engine

from .tables import build_metadata, get_table


class CepQuerier:
    def __init__(self, database_url: str, cep_table_name: str | None = None):
        self.engine = create_engine(database_url, echo=False)

        if cep_table_name:
            metadata = build_metadata({"cep_unificado": cep_table_name})
        else:
            metadata = build_metadata()

        self.cep_table = get_table(metadata, "cep_unificado")

    def query(self, cep: str) -> dict | None:
        cep = cep.replace("-", "").strip()

        with self.engine.connect() as conn:
            cep = conn.execute(
                self.cep_table.select().where(self.cep_table.c.cep == cep)
            ).first()

            return cep._asdict() if cep else None
