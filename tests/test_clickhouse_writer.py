"""
Testes para o módulo ClickHouseWriter.

Os testes verificam a funcionalidade de escrita de dados
e-DNE em bases ClickHouse.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from edne_correios_loader import TableSetEnum, ClickHouseWriter
from edne_correios_loader.tables import get_table, metadata


class TestClickHouseWriterConnection:
    """Testes de conexão e desconexão do ClickHouseWriter"""

    def test_clickhouse_writer_initialization(self):
        """Testa inicialização do escritor ClickHouse"""
        writer = ClickHouseWriter(
            host="localhost",
            port=9000,
            database="test_db",
            user="default",
            password="",
        )
        
        assert writer.host == "localhost"
        assert writer.port == 9000
        assert writer.database == "test_db"
        assert writer.user == "default"
        assert writer.password == ""
        assert writer.metadata is not None

    def test_clickhouse_writer_parse_host_with_port(self):
        """Testa resolução de host:porta no argumento de host."""
        writer = ClickHouseWriter(host="example.com:8123")

        assert writer.host == "example.com"
        assert writer.port == 8123
        assert writer.interface == "http"

    def test_clickhouse_writer_parse_http_url(self):
        """Testa resolução de URL HTTP no argumento de host."""
        writer = ClickHouseWriter(host="http://example.com")

        assert writer.host == "example.com"
        assert writer.port == 8123
        assert writer.interface == "http"

    def test_clickhouse_writer_parse_https_url(self):
        """Testa resolução de URL HTTPS no argumento de host."""
        writer = ClickHouseWriter(host="https://example.com")

        assert writer.host == "example.com"
        assert writer.port == 8443
        assert writer.interface == "http"
        assert writer.secure is True

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_clickhouse_writer_context_manager(self, mock_client):
        """Testa o gerenciador de contexto"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        with writer:
            assert writer.client is not None
            mock_instance.execute.assert_called_once_with("SELECT 1")
        
        mock_instance.disconnect.assert_called_once()

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_clickhouse_writer_disconnect_on_error(self, mock_client):
        """Testa desconexão quando há erro"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        try:
            with writer:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        mock_instance.disconnect.assert_called_once()


class TestClickHouseWriterTableOperations:
    """Testes de operações em tabelas do ClickHouse"""

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_create_tables(self, mock_client):
        """Testa criação de tabelas"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        with writer:
            tables_to_create = ["log_localidade", "log_bairro"]
            writer.create_tables(tables_to_create)
            
            # Verifica se execute foi chamado para cada tabela
            assert mock_instance.execute.call_count >= len(tables_to_create)

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_clean_tables(self, mock_client):
        """Testa limpeza de tabelas"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        with writer:
            tables_to_clean = ["log_localidade", "log_bairro"]
            writer.clean_tables(tables_to_clean)
            
            # Verifica se TRUNCATE foi executado
            calls = mock_instance.execute.call_args_list
            truncate_calls = [
                c for c in calls if "TRUNCATE" in str(c)
            ]
            assert len(truncate_calls) >= len(tables_to_clean)

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_drop_tables(self, mock_client):
        """Testa remoção de tabelas"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        with writer:
            tables_to_drop = ["log_localidade", "log_bairro"]
            writer.drop_tables(tables_to_drop)
            
            # Verifica se DROP TABLE foi executado
            calls = mock_instance.execute.call_args_list
            drop_calls = [
                c for c in calls if "DROP" in str(c)
            ]
            assert len(drop_calls) >= len(tables_to_drop)

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_drop_tables_empty_list(self, mock_client):
        """Testa remoção com lista vazia"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        with writer:
            writer.drop_tables([])
            # Não deve executar nada além da verificação de conexão
            assert mock_instance.execute.call_count == 1


class TestClickHouseWriterDataPopulation:
    """Testes de população de dados"""

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_populate_table(self, mock_client):
        """Testa população de tabela"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        # Prepara dados de teste
        test_data = [
            ["1", "Localidade 1", "SP", "3550308", "0"],
            ["2", "Localidade 2", "RJ", "3300100", "0"],
        ]
        
        with writer:
            writer.populate_table("log_localidade", test_data)
            
            # Verifica se execute foi chamado para inserção
            insert_calls = [
                c for c in mock_instance.execute.call_args_list
                if "INSERT" in str(c)
            ]
            assert len(insert_calls) >= 1

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_populate_table_with_batch_size(self, mock_client):
        """Testa população com diferentes tamanhos de lote"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        writer.insert_buffer_size = 5
        
        # Cria 15 linhas de dados (3 lotes de 5)
        test_data = [
            [str(i), f"Localidade {i}", "SP", "3550308", "0"]
            for i in range(15)
        ]
        
        with writer:
            writer.populate_table("log_localidade", test_data)
            
            # Verifica se execute foi chamado para inserções
            insert_calls = [
                c for c in mock_instance.execute.call_args_list
                if "INSERT" in str(c)
            ]
            # Deve ter pelo menos 3 INSERT (um por lote)
            assert len(insert_calls) >= 3

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_populate_table_invalid_table(self, mock_client):
        """Testa população com tabela inválida"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        test_data = [["1", "test", "data"]]
        
        with writer:
            # Não deve lançar erro, mas registra aviso
            writer.populate_table("invalid_table", test_data)
            
            # Não deve fazer insert
            insert_calls = [
                c for c in mock_instance.execute.call_args_list
                if "INSERT" in str(c)
            ]
            assert len(insert_calls) == 0

    @patch("edne_correios_loader.clickhouse_writer.Client")
    def test_populate_unified_table(self, mock_client):
        """Testa população da tabela unificada"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        writer = ClickHouseWriter()
        
        with writer:
            writer.populate_unified_table()

            # Deve executar TRUNCATE e INSERT ... SELECT
            calls = mock_instance.execute.call_args_list
            truncate_calls = [
                c for c in calls
                if "TRUNCATE TABLE cep_unificado" in str(c)
            ]

            insert_calls = [
                c for c in calls
                if "INSERT INTO cep_unificado" in str(c)
            ]

            assert len(truncate_calls) >= 1
            assert len(insert_calls) >= 1


class TestClickHouseWriterTypeConversion:
    """Testes de conversão de tipos"""

    def test_get_clickhouse_type_integer(self):
        """Testa conversão de tipos INTEGER"""
        from sqlalchemy import Integer, Column
        
        col = Column("test", Integer)
        result = ClickHouseWriter._get_clickhouse_type(col)
        
        assert result == "Int32"

    def test_get_clickhouse_type_string(self):
        """Testa conversão de tipos String"""
        from sqlalchemy import String, Column
        
        col = Column("test", String(255))
        result = ClickHouseWriter._get_clickhouse_type(col)
        
        assert result == "String"

    def test_get_clickhouse_type_varchar(self):
        """Testa conversão de tipos VARCHAR"""
        from sqlalchemy import VARCHAR, Column
        
        col = Column("test", VARCHAR(100))
        result = ClickHouseWriter._get_clickhouse_type(col)
        
        assert result == "String"

    def test_get_clickhouse_type_default(self):
        """Testa conversão padrão para tipos desconhecidos"""
        from sqlalchemy import Column, types
        
        class UnknownType(types.TypeEngine):
            pass
        
        col = Column("test", UnknownType())
        result = ClickHouseWriter._get_clickhouse_type(col)
        
        assert result == "String"


class TestClickHouseWriterSQLGeneration:
    """Testes de geração de SQL"""

    def test_build_create_table_sql_simple(self):
        """Testa geração de CREATE TABLE Simple"""
        from sqlalchemy import Table, Column, Integer, String, MetaData
        
        test_metadata = MetaData()
        test_table = Table(
            "test_table",
            test_metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(100)),
        )
        
        writer = ClickHouseWriter()
        sql = writer._build_create_table_sql("test_table", test_table)
        
        assert "CREATE TABLE IF NOT EXISTS test_table" in sql
        assert "Int32" in sql
        assert "String" in sql
        assert "PRIMARY KEY" in sql
        assert "ORDER BY" in sql

    def test_build_create_table_sql_nullable_columns(self):
        """Testa geração com colunas nullable"""
        from sqlalchemy import Table, Column, Integer, String, MetaData
        
        test_metadata = MetaData()
        test_table = Table(
            "test_table",
            test_metadata,
            Column("id", Integer, primary_key=True, nullable=False),
            Column("optional", String(100), nullable=True),
        )
        
        writer = ClickHouseWriter()
        sql = writer._build_create_table_sql("test_table", test_table)
        
        assert "Nullable(String)" in sql
        # ID deve ser non-nullable
        assert sql.count("Nullable") >= 1


class TestClickHouseWriterIntegration:
    """Testes de integração (se ClickHouse está disponível)"""

    @pytest.mark.skipif(
        not os.environ.get("CLICKHOUSE_HOST"),
        reason="ClickHouse não está configurado"
    )
    def test_clickhouse_real_connection(self):
        """Testa conexão real com ClickHouse"""
        host = os.environ.get("CLICKHOUSE_HOST", "localhost")
        port = int(os.environ.get("CLICKHOUSE_PORT", 9000))
        
        writer = ClickHouseWriter(host=host, port=port)
        
        with writer:
            # Se chegou aqui, conexão foi bem-sucedida
            assert writer.client is not None

    @pytest.mark.skipif(
        not os.environ.get("CLICKHOUSE_HOST"),
        reason="ClickHouse não está configurado"
    )
    def test_clickhouse_real_table_creation(self):
        """Testa criação real de tabela em ClickHouse"""
        host = os.environ.get("CLICKHOUSE_HOST", "localhost")
        port = int(os.environ.get("CLICKHOUSE_PORT", 9000))
        database = os.environ.get("CLICKHOUSE_DATABASE", "default")
        
        writer = ClickHouseWriter(host=host, port=port, database=database)
        
        with writer:
            writer.create_tables(["log_localidade"])
            writer.drop_tables(["log_localidade"])
