from bookrec.db_manager import SQLiteDBM
from bookrec.rec_engine import Recommender

import streamlit as st

SQLITE_PATH = "book_rec.db"


def main():
    dbm = SQLiteDBM(SQLITE_PATH)
    try:
        entry(dbm)
    finally:
        dbm._con.close()


def entry(dbm):
    rec = Recommender(dbm)

    st.title("Book recommender")

    titles = rec._books["Book-Title"].unique()
    authors = rec._books["Book-Author"].unique()

    title = st.selectbox(
        "Choose one book title to base your recommendations on:",
        titles
        )
    
    author = st.selectbox(
        "Choose the books author to base your recommendations on:",
        authors
    )

    def get_rec():
        recs = rec.recommend(title, author)
        if len(recs) > 0:
            st.write("Showing recommendations for:")
            st.write(f"{title}, by {author}")
            st.write(recs)

    st.button("Get recommendations", on_click=get_rec)


if __name__ == "__main__":
    main()