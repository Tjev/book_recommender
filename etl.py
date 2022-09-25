import os
import requests
import sqlite3
import zipfile

import pandas as pd

ZIPPED_DATA_URL = "http://www2.informatik.uni-freiburg.de/~cziegler/BX/BX-CSV-Dump.zip"
ZIP_FILE = "BX-CSV-Dump.zip"
DATA_DIR = "data/"

# Prepare a download function
def download_file(url):
    local_filename = url.split("/")[-1]
    r = requests.get(url, stream=True)

    i = 0
    chunk_size = 1024**2
    with open(local_filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if i % 10 == 0:
                print(f"downloaded {i} MB's")
            if chunk:
                f.write(chunk)
            i += 1


# Download the zipped dataset using the prepared download function
download_file(ZIPPED_DATA_URL)

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

with zipfile.ZipFile(ZIP_FILE, "r") as zf:
    zf.extractall(DATA_DIR)

ratings_df = pd.read_csv("data/BX-Book-Ratings.csv", encoding="cp1251", sep=";")
books_df = pd.read_csv("data/BX-Books.csv", encoding="cp1251", sep=";", escapechar="\\")

# Drop implicit ratings
ratings_df = ratings_df[ratings_df["Book-Rating"] != 0]

# Drop redundant columns and retype the rest into strings
books_df = books_df[["ISBN", "Book-Title", "Book-Author"]]
books_df = books_df.astype(
    {"ISBN": "string", "Book-Title": "string", "Book-Author": "string"}
)

# Set title and author to lowercase and remove preceding/trailing whitespace
books_df["Book-Title"] = books_df["Book-Title"].str.lower().str.strip()
books_df["Book-Author"] = books_df["Book-Author"].str.lower().str.strip()
# Replace multiple whitespaces with single " "
books_df["Book-Title"] = books_df["Book-Title"].str.replace(r"\s+", " ", regex=True)
books_df["Book-Author"] = books_df["Book-Author"].str.replace(r"\s+", " ", regex=True)
# Add whitespace after dot in names (e.g.: "j.r.r. Tolkien" -> "j. r. r. Tolkien")
books_df["Book-Title"] = books_df["Book-Title"].str.replace(
    r"\.(?=\S)", ". ", regex=True
)
books_df["Book-Author"] = books_df["Book-Author"].str.replace(
    r"\.(?=\S)", ". ", regex=True
)

df = ratings_df.merge(books_df, on="ISBN")

# Retype once again
obj_cols = [col for col in df.columns if pd.api.types.is_object_dtype(df[col])]
df = df.astype({col: "string" for col in obj_cols})

# Dedupe by ISBN, save ISBN with highest amount of ratings assigned to it
cdf = (
    df[["ISBN", "Book-Title", "Book-Author", "Book-Rating"]]
    .groupby(["Book-Title", "Book-Author", "ISBN"])
    .count()
    .reset_index()
)
cdf = cdf.sort_values(
    ["Book-Title", "Book-Author", "Book-Rating"], ascending=False
).drop_duplicates(["Book-Title", "Book-Author"])

# DEMO ONLY:
popular_cdf = cdf[cdf["Book-Rating"] > 10].drop("Book-Rating", axis=1)
# ---------

cdf = cdf.drop("Book-Rating", axis=1)

df = df.drop("ISBN", axis=1)
df = df.merge(cdf, on=["Book-Title", "Book-Author"])

# Dedupe user-isbn ratings by computing the mean
df = df.groupby(["User-ID", "ISBN"])["Book-Rating"].mean().to_frame().reset_index()

# Load into database
with sqlite3.connect("books_ratings.db") as con:
    df.to_sql("ratings", con, if_exists="replace")
    cdf.to_sql("books", con, if_exists="replace")
    popular_cdf.to_sql("demo_popular_books", con, if_exists="replace")
