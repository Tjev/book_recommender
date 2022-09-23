import pandas as pd

from book_rec.db_connector import DBConnector


class RecEngine:
    def __init__(self, db_connector: DBConnector, threshold: int = 8):
        self._con = db_connector
        self._threshold = threshold
        self._init_dfs()

    def _init_dfs(self) -> None:
        self._rating_df = self._con.load_table("ratings")
        self._books_df = self._con.load_table("books")

        rating_counts = self._rating_df.groupby(["ISBN"]).agg("count").reset_index()
        isbns = rating_counts["ISBN"][rating_counts["User-ID"] >= self._threshold]
        self.book_opts = self._books_df.merge(isbns, on="ISBN")

    def recommend(self, title: str, author: str, k: int = 10):
        isbn_query = self._books_df[
            (self._books_df["Book-Title"] == title)
            & (self._books_df["Book-Author"] == author)
        ]["ISBN"]
        if len(isbn_query) == 0:
            return "No such book has been found."
        isbn = isbn_query.values[0]

        book_readers = self._rating_df[self._rating_df["ISBN"] == isbn]["User-ID"]
        book_readers = book_readers.unique()

        # Final dataset
        relevant_ratings = self._rating_df[
            self._rating_df["User-ID"].isin(book_readers)
        ]

        # Number of ratings per other books in dataset
        ratings_per_book = relevant_ratings.groupby(["ISBN"]).agg("count").reset_index()

        # Select only books which have actually higher number of ratings than threshold
        books_to_compare = ratings_per_book["ISBN"][
            ratings_per_book["User-ID"] >= self._threshold
        ].values

        ratings_data_raw = relevant_ratings[
            relevant_ratings["ISBN"].isin(books_to_compare)
        ]

        # Group by User and Book and compute mean
        ratings_data_raw_nodup = (
            ratings_data_raw.groupby(["User-ID", "ISBN"])["Book-Rating"]
            .mean()
            .reset_index()
        )

        # Prepare the pivot table used to calculate the correlations
        rating_mtx = ratings_data_raw_nodup.pivot(
            index="User-ID", columns="ISBN", values="Book-Rating"
        )

        # Take out the selected book from the pivot table
        dataset_of_other_books = rating_mtx.copy(deep=False)
        dataset_of_other_books.drop([isbn], axis=1, inplace=True)

        book_isbns = dataset_of_other_books.columns.values
        corrs = dataset_of_other_books.corrwith(rating_mtx[isbn]).values
        avgs = ratings_data_raw.groupby("ISBN")["Book-Rating"].mean().drop(isbn)

        topk_df = (
            pd.DataFrame({"ISBN": book_isbns, "corr": corrs, "avg": avgs})
            .reset_index(drop=True)
            .sort_values("corr", ascending=False)
            .head(k)
        )

        # Add additional book information into the result dataframe
        return topk_df.merge(self._books_df, on="ISBN")[
            ["Book-Title", "Book-Author", "ISBN", "corr", "avg"]
        ]
