import os
import requests
import sqlite3
import zipfile

import pandas as pd

ZIPPED_DATA_URL = "http://www2.informatik.uni-freiburg.de/~cziegler/BX/BX-CSV-Dump.zip"
ZIPPED_DATA_PATH = "BX-CSV-Dump.zip"
DATA_DIR = "data/"

# Prepare a download function
def download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    
    i = 0
    chunk_size = 1024**2
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if i % 10 == 0:
                print(f'downloaded {i} MB\'s')
            if chunk:
                f.write(chunk)
            i += 1

    print(f"Download of {local_filename} complete!")

download_file(ZIPPED_DATA_URL)

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

with zipfile.ZipFile(ZIPPED_DATA_PATH, 'r') as f:
    f.extractall(DATA_DIR)


# Load the dataframes

book_rating_df = pd.read_csv("data/BX-Book-Ratings.csv", encoding="cp1251", sep=";")

# Drop implicit ratings
book_rating_df = book_rating_df[book_rating_df["Book-Rating"] != 0]

books_df = pd.read_csv("data/BX-Books.csv", encoding="cp1251", sep=";", escapechar="\\")

# Drop redundant columns and retype the rest into strings
books_df = books_df[["ISBN", "Book-Title", "Book-Author"]]
books_df = books_df.astype({'ISBN': 'string', 'Book-Title': 'string', 'Book-Author': 'string'})

books_df.fillna("Unknown", inplace=True)

# First we will convert both the book titles and book authors
# into lowercase (to improve the effects of later deduplication).
books_df["Book-Title"] = books_df["Book-Title"].apply(str.lower).str.strip()
books_df["Book-Author"] = books_df["Book-Author"].str.lower().str.strip()

# In case of authors, we also need to get rid of extra whitespaces.
books_df["Book-Author"] = books_df["Book-Author"].str.replace(' +', ' ', regex=True)
# Also, add the missing whitespaces after abbreviated names (e.g.: "j.r.r tolkien" -> "j. r. r. tolkien")
books_df["Book-Author"] = books_df["Book-Author"].str.replace(r'\.(?=\S)', '. ', regex=True)

df = book_rating_df.merge(books_df, on="ISBN")
df = df.astype({"ISBN": "string", "Book-Title": "string", "Book-Author": "string"})

dfc = df.groupby(["Book-Title", "Book-Author", "ISBN"]).count().reset_index()
# Take the ISBNs with the highest amount of reviews
dfcs = dfc.sort_values(["Book-Title", "Book-Author", "User-ID"], ascending=False).groupby(["Book-Title", "Book-Author"]).head(1)

most_popular_isbn_df = dfcs[["Book-Title", "Book-Author", "ISBN"]]
df = df.merge(most_popular_isbn_df, on=["Book-Title", "Book-Author"], suffixes=("_original", ""))

# Drop all the redundant columns
df = df[["User-ID", "Book-Rating", "ISBN"]]

# de-dupe user-isbn ratings by computing the mean
df = df.groupby(["User-ID", "ISBN"])["Book-Rating"].mean().to_frame().reset_index()

# load the cleaned data into database (PoC: sqlite3)
con = sqlite3.connect("book_rec.db")

df.to_sql("book_ratings", con, if_exists="replace", index=False)
most_popular_isbn_df.to_sql("books", con, if_exists="replace", index=False)

con.commit()
con.close()