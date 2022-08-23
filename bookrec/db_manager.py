import sqlite3

import pandas as pd

class DBManager():
    def load_table(self, table: str) -> pd.DataFrame:
        if isinstance(self, DBManager):
            raise NotImplementedError()


class SQLiteDBM(DBManager):
    def __init__(self, db_path: str):
        self._con = sqlite3.connect(db_path)

    def load_table(self, table: str) -> pd.DataFrame:
        return pd.read_sql_query(f"SELECT * FROM {table}", self._con)