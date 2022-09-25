import sqlite3
import pandas as pd


class DBConnector:
    def load_table(self, table: str):
        raise NotImplementedError()


class SQLiteConnector(DBConnector):
    def __init__(self, connection: sqlite3.Connection):
        self._con = connection

    def load_table(self, table: str):
        return pd.read_sql_query(f"SELECT * FROM {table};", self._con)

    def close(self):
        self._con.close()
