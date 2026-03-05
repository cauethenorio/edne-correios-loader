import logging
from collections.abc import Iterable, Iterator

import sqlalchemy as sa
from sqlalchemy import MetaData

from .tables import get_table
from .tables import metadata as default_metadata

logger = logging.getLogger(__name__)


def cep_unificado_insert_from(cep_unificado, rows: "sa.Select"):
    return cep_unificado.insert().from_select(rows.selected_columns, rows.subquery())


def normalize_logradouro(rows: "sa.CursorResult") -> Iterator[dict]:
    for row in rows:
        logradouro_parts = row.logradouro.split(",", 1)

        yield {
            **row._asdict(),
            "logradouro": logradouro_parts[0].strip(),
            "complemento": logradouro_parts[1].strip()
            if len(logradouro_parts) > 1
            else None,
        }


def cep_unificado_insert_in_batches(
    conn: sa.Connection, cep_unificado, rows: Iterable[dict], batch_size: int = 500
):
    """
    Insert rows in the unified table in batches
    """
    batch = []

    for row in rows:
        batch.append(row)

        if len(batch) == batch_size:
            logger.debug("Inserting %d rows into cep_unificado", len(batch))
            conn.execute(cep_unificado.insert().values(batch))
            batch = []

    if batch:
        logger.debug("Inserting %d rows into cep_unificado", len(batch))
        conn.execute(cep_unificado.insert().values(batch))


def select_logradouros_ceps(metadata) -> "sa.Select":
    log_logradouro = get_table(metadata, "log_logradouro")
    log_bairro = get_table(metadata, "log_bairro")
    log_localidade = get_table(metadata, "log_localidade")

    return sa.select(
        log_logradouro.c.cep.label("cep"),
        sa.case(
            (
                log_logradouro.c.log_sta_tlo == "S",
                log_logradouro.c.tlo_tx + " " + log_logradouro.c.log_no,
            ),
            else_=log_logradouro.c.log_no,
        ).label("logradouro"),
        log_bairro.c.bai_no.label("bairro"),
        log_localidade.c.loc_no.label("municipio"),
        log_localidade.c.mun_nu.label("municipio_cod_ibge"),
        log_logradouro.c.ufe_sg.label("uf"),
    ).select_from(
        log_logradouro.join(log_localidade).join(
            log_bairro, onclause=log_logradouro.c.bai_nu_ini == log_bairro.c.bai_nu
        )
    )


def select_localidades_ceps(metadata) -> "sa.Select":
    log_localidade = get_table(metadata, "log_localidade")

    return (
        sa.select(
            log_localidade.c.cep.label("cep"),
            log_localidade.c.ufe_sg.label("uf"),
            log_localidade.c.loc_no.label("municipio"),
            log_localidade.c.mun_nu.label("municipio_cod_ibge"),
        )
        .select_from(log_localidade)
        .where(
            log_localidade.c.cep.isnot(None)
            & log_localidade.c.loc_nu_sub.is_(None)
            & log_localidade.c.mun_nu.isnot(None),
        )
    )


def select_localidades_subordinadas_ceps(metadata) -> "sa.Select":
    log_localidade = get_table(metadata, "log_localidade")
    localidade_subordinada = log_localidade.alias()

    return (
        sa.select(
            log_localidade.c.cep.label("cep"),
            log_localidade.c.ufe_sg.label("uf"),
            localidade_subordinada.c.loc_no.label("municipio"),
            localidade_subordinada.c.mun_nu.label("municipio_cod_ibge"),
            log_localidade.c.loc_no.label("bairro"),
        )
        .select_from(log_localidade)
        .join(
            localidade_subordinada,
            onclause=log_localidade.c.loc_nu_sub == localidade_subordinada.c.loc_nu,
        )
        .where(
            log_localidade.c.cep.isnot(None)
            & log_localidade.c.loc_nu_sub.isnot(None)
            & localidade_subordinada.c.mun_nu.isnot(None),
        )
    )


def select_cpc_ceps(metadata) -> "sa.Select":
    log_cpc = get_table(metadata, "log_cpc")
    log_localidade = get_table(metadata, "log_localidade")
    localidade_subordinada = log_localidade.alias()

    return (
        sa.select(
            log_cpc.c.cep.label("cep"),
            log_cpc.c.cpc_endereco.label("logradouro"),
            sa.func.coalesce(
                localidade_subordinada.c.loc_no,
                log_localidade.c.loc_no,
            ).label("municipio"),
            sa.func.coalesce(
                localidade_subordinada.c.mun_nu,
                log_localidade.c.mun_nu,
            ).label("municipio_cod_ibge"),
            log_cpc.c.ufe_sg.label("uf"),
            log_cpc.c.cpc_no.label("nome"),
        )
        .select_from(log_cpc)
        .join(log_localidade)
        .outerjoin(
            localidade_subordinada,
            onclause=log_localidade.c.loc_nu_sub == localidade_subordinada.c.loc_nu,
        )
    )


def select_grandes_usuarios_ceps(metadata) -> "sa.Select":
    log_grande_usuario = get_table(metadata, "log_grande_usuario")
    log_bairro = get_table(metadata, "log_bairro")
    log_localidade = get_table(metadata, "log_localidade")
    localidade_subordinada = log_localidade.alias()

    return (
        sa.select(
            log_grande_usuario.c.cep.label("cep"),
            log_grande_usuario.c.gru_endereco.label("logradouro"),
            log_bairro.c.bai_no.label("bairro"),
            sa.func.coalesce(
                localidade_subordinada.c.loc_no,
                log_localidade.c.loc_no,
            ).label("municipio"),
            sa.func.coalesce(
                localidade_subordinada.c.mun_nu,
                log_localidade.c.mun_nu,
            ).label("municipio_cod_ibge"),
            log_grande_usuario.c.ufe_sg.label("uf"),
            log_grande_usuario.c.gru_no.label("nome"),
        )
        .select_from(log_grande_usuario)
        .join(log_localidade)
        .join(log_bairro, onclause=log_grande_usuario.c.bai_nu == log_bairro.c.bai_nu)
        .outerjoin(
            localidade_subordinada,
            onclause=log_localidade.c.loc_nu_sub == localidade_subordinada.c.loc_nu,
        )
    )


def select_unidades_operacionais_ceps(metadata) -> "sa.Select":
    log_unid_oper = get_table(metadata, "log_unid_oper")
    log_bairro = get_table(metadata, "log_bairro")
    log_localidade = get_table(metadata, "log_localidade")
    localidade_subordinada = log_localidade.alias()

    return (
        sa.select(
            log_unid_oper.c.cep.label("cep"),
            log_unid_oper.c.uop_endereco.label("logradouro"),
            log_bairro.c.bai_no.label("bairro"),
            sa.func.coalesce(
                localidade_subordinada.c.loc_no,
                log_localidade.c.loc_no,
            ).label("municipio"),
            sa.func.coalesce(
                localidade_subordinada.c.mun_nu,
                log_localidade.c.mun_nu,
            ).label("municipio_cod_ibge"),
            log_unid_oper.c.ufe_sg.label("uf"),
            log_unid_oper.c.uop_no.label("nome"),
        )
        .select_from(log_unid_oper)
        .join(log_localidade)
        .join(log_bairro, onclause=log_unid_oper.c.bai_nu == log_bairro.c.bai_nu)
        .outerjoin(
            localidade_subordinada,
            onclause=log_localidade.c.loc_nu_sub == localidade_subordinada.c.loc_nu,
        )
        .where(
            sa.func.coalesce(
                localidade_subordinada.c.mun_nu,
                log_localidade.c.mun_nu,
            ).isnot(None)
        )
    )


def populate_unified_table(
    conn: sa.Connection,
    metadata: MetaData = default_metadata,
    insert_batch_size: int = 500,
):
    """
    Query unifying rows from all tables with CEP address information
    """
    cep_unificado = get_table(metadata, "cep_unificado")

    insert_from_selects = [
        (select_logradouros_ceps(metadata), "logradouros"),
        (select_localidades_ceps(metadata), "localidades"),
        (select_localidades_subordinadas_ceps(metadata), "localidades subordinadas"),
    ]

    for select_stmt, name in insert_from_selects:
        logger.info(
            "Populating unified CEP table with %s data",
            name,
            extra={"indentation": 1},
        )
        conn.execute(cep_unificado_insert_from(cep_unificado, select_stmt))

        inserted = conn.execute(
            sa.select(sa.func.count()).select_from(select_stmt.subquery())
        ).scalar()

        logger.info(
            "Inserted %s CEPs from %s into table %s",
            inserted,
            name,
            cep_unificado.name,
            extra={"indentation": 2},
        )

    # the following ones need some normalization before inserting
    # they are normalized via python, so this can run for different DBMSs

    selects_with_normalization = [
        (select_cpc_ceps(metadata), "CPC"),
        (select_grandes_usuarios_ceps(metadata), "grandes usuários"),
        (select_unidades_operacionais_ceps(metadata), "unidades operacionais"),
    ]

    for select_stmt, name in selects_with_normalization:
        logger.info(
            "Populating unified CEP table with normalized %s data",
            name,
            extra={"indentation": 1},
        )

        cep_unificado_insert_in_batches(
            conn,
            cep_unificado,
            normalize_logradouro(conn.execute(select_stmt).yield_per(1000)),
            batch_size=insert_batch_size,
        )

        inserted = conn.execute(
            sa.select(sa.func.count()).select_from(select_stmt.subquery())
        ).scalar()

        logger.info(
            "Inserted %s CEPs from %s into table %s",
            inserted,
            name,
            cep_unificado.name,
            extra={"indentation": 2},
        )

    inserted = conn.execute(
        sa.select(sa.func.count()).select_from(cep_unificado)
    ).scalar()

    logger.info(
        'Inserted %s rows into table "%s"',
        inserted,
        cep_unificado.name,
        extra={"indentation": 1},
    )
