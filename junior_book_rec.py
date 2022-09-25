import numpy as np
import pandas as pd

LOR_BOOK = "the fellowship of the ring (the lord of the rings, part 1)"

# load ratings
ratings = pd.read_csv("BX-Book-Ratings.csv", encoding="cp1251", sep=";")
ratings = ratings[ratings["Book-Rating"] != 0]

# load books
books = pd.read_csv("BX-Books.csv", encoding="cp1251", sep=";", error_bad_lines=False)

# TOMAS - I would drop unnecessary columns from the book dataframe before merging
dataset = pd.merge(ratings, books, on=["ISBN"])
# TOMAS - after merging I would retype all the relevant dataframes
dataset_lowercase = dataset.apply(
    lambda x: x.str.lower() if (x.dtype == "object") else x
)

tolkien_readers = dataset_lowercase["User-ID"][
    (dataset_lowercase["Book-Title"] == LOR_BOOK)
    & (dataset_lowercase["Book-Author"].str.contains("tolkien"))
]
tolkien_readers = tolkien_readers.unique()

# final dataset
books_of_tolkien_readers = dataset_lowercase[
    dataset_lowercase["User-ID"].isin(tolkien_readers)
]

# Number of ratings per other books in dataset
number_of_rating_per_book = (
    books_of_tolkien_readers.groupby(["Book-Title"]).agg("count").reset_index()
)

# select only books which have actually higher number of ratings than threshold
books_to_compare = number_of_rating_per_book["Book-Title"][
    number_of_rating_per_book["User-ID"] >= 8
].values

ratings_data_raw = books_of_tolkien_readers[["User-ID", "Book-Rating", "Book-Title"]][
    books_of_tolkien_readers["Book-Title"].isin(books_to_compare)
]

# group by User and Book and compute mean
ratings_data_raw_nodup = (
    ratings_data_raw.groupby(["User-ID", "Book-Title"])["Book-Rating"]
    .mean()
    .reset_index()
)

dataset_for_corr = ratings_data_raw_nodup.pivot(
    index="User-ID", columns="Book-Title", values="Book-Rating"
)

LoR_list = [LOR_BOOK]

result_list = []
worst_list = []

# for each of the trilogy book compute:
for LoR_book in LoR_list:

    # Take out the Lord of the Rings selected book from correlation dataframe
    dataset_of_other_books = dataset_for_corr.copy(deep=False)
    dataset_of_other_books.drop([LoR_book], axis=1, inplace=True)

    # TOMAS - we can omptimize this
    book_titles = dataset_of_other_books.columns.values
    corrs = dataset_of_other_books.corrwith(dataset_for_corr[LoR_book]).values
    avgs = (
        ratings_data_raw[ratings_data_raw["Book-Title"] != LoR_book]
        .groupby("Book-Title")
        .mean()
        .reset_index()["Book-Rating"]
        .values
    )

    corr_fellowship = pd.DataFrame({"titles": book_titles, "corr": corrs, "avg": avgs})

    # TOMAS - I am not sure if sorting and then appending makes much sense here...
    #         Maybe I would create a larger list and then sort?

    # top 10 books with highest corr
    result_list.append(corr_fellowship.sort_values("corr", ascending=False).head(10))

    # worst 10 books
    worst_list.append(corr_fellowship.sort_values("corr", ascending=False).tail(10))

print("Correlation for book:", LoR_list[0])
print(
    "Average rating of LOR:",
    ratings_data_raw[ratings_data_raw["Book-Title"] == LOR_BOOK]
    .groupby(ratings_data_raw["Book-Title"])
    .mean(),
)
rslt = result_list[0]
