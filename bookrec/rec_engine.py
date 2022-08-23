#from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

from bookrec.db_manager import DBManager


class Recommender():
    def __init__(self, db_manager: DBManager, threshold: int = 8):
        self._books = db_manager.load_table("books")
        self._ratings = db_manager.load_table("book_ratings")
        # self._drop_sparse_entries(threshold)

    def _drop_sparse_entries(self, threshold):
        ratings_per_book = self._ratings.groupby(["ISBN"]).agg("count").reset_index()
        # Get all the book entries with more than "threshold" reviews
        s = ratings_per_book["ISBN"][ratings_per_book["User-ID"] >= threshold]
        # Keep only the books and reviews of books which have more than "threshold" total reviews
        self._ratings = self._ratings[self._ratings["ISBN"].isin(s)]
        self._books = self._books[self._books["ISBN"].isin(s)]

    def recommend(self, title: str, author: str, k: int = 10, threshold: int = 2) -> pd.DataFrame:
        isbn = self._lookup_isbn_by_title(title, author)
        if not isbn:
            return "No such book has been found."

        # Lookup readers of the base book:
        simillar_readers = self._ratings["User-ID"][self._ratings["ISBN"].values == isbn]
        simillar_readers = simillar_readers.unique()

        simillar_readers_ratings = self._ratings[(self._ratings["User-ID"].isin(simillar_readers))]

        ratings_per_book = simillar_readers_ratings.groupby(["ISBN"]).agg("count").reset_index()

        # Do not consider books with amount of reviews under the threshold
        books_to_compare = ratings_per_book["ISBN"][ratings_per_book["User-ID"] >= threshold]
        books_to_compare = books_to_compare.tolist()

        # Choose only relevant subset of ratings
        ratings_data_raw = simillar_readers_ratings[simillar_readers_ratings["ISBN"].isin(books_to_compare)]

        # Prepare the pivot table used to calculate the correlations
        ratings_mtx = ratings_data_raw.pivot(index="User-ID", columns="ISBN", values="Book-Rating")

        # Take out the selected book from the pivot table
        dataset_of_other_books = ratings_mtx.copy(deep=False)
        dataset_of_other_books.drop([isbn], axis=1, inplace=True)

        isbns = dataset_of_other_books.columns.values
        correlations = dataset_of_other_books.corrwith(ratings_mtx[isbn])
        avg_ratings = ratings_data_raw.groupby("ISBN")["Book-Rating"].mean().drop(isbn)

        corr_df = pd.DataFrame(
            {"book": isbns, "corr": correlations, "avg_rating": avg_ratings}
            ).reset_index(drop=True)

        topk_isbns = corr_df.sort_values("corr", ascending=False).head(k)
        return self._lookup_books_by_isbns(topk_isbns["book"].values)
        # return topk_isbns

    def _lookup_book_by_isbn(self, isbn: str) -> tuple[str, str]:
        # Look-up of a book title and author based on its ISBN code.
        mask = self._books["ISBN"].values == isbn
        res = self._books[mask].values[0]
        return res[0], res[1]

    def _lookup_books_by_isbns(self, lookup_isbns: np.ndarray) -> pd.DataFrame:
        # Look-up of a book title and author based on its ISBN code.
        # We build the dataframe incrementaly in order to retain the ordering.
        titles = list()
        authors = list()
        isbns = list()
        for i_isbn in lookup_isbns:
            row = self._books[self._books["ISBN"].values == i_isbn].values[0]
            title, author, isbn = row
            titles.append(title)
            authors.append(author)
            isbns.append(isbn)
        
        return pd.DataFrame(data = {"Book-Title": titles, "Book-Author": authors, "ISBN": isbns})
    
    def _lookup_isbn_by_title(self, title: str, author: str) -> str:
        # Look-up of a book ISBN code based on its title and author.
        mask = (self._books["Book-Title"].values == title.strip()) & (self._books["Book-Author"].values == author.strip())
        res = self._books["ISBN"][mask]
        if len(res) > 0:
            return res.values[0]
        return None
