import sqlite3
from book_rec.db_connector import SQLiteConnector
from book_rec.recommender import RecEngine

import streamlit as st


def main():
    con = sqlite3.connect("file:books_ratings.db?mode=ro", uri=True)
    dbc = SQLiteConnector(con)
    try:
        entry(dbc)
    finally:
        dbc.close()


def entry(dbc):
    rec = RecEngine(dbc)

    st.title("Book recommender")

    # Set up initial state of the app
    if "popular_books_cache" not in st.session_state:
        popular_books = dbc.load_table("demo_popular_books")
        st.session_state.popular_books_cache = popular_books
        st.session_state.titles_cache = popular_books["Book-Title"].unique()
        st.session_state.authors_cache = popular_books["Book-Author"].unique()

    title = st.selectbox(
        "Choose one book title to base your recommendations on:",
        st.session_state.titles_cache,
        key="title_selectbox",
    )

    # Set up author field container and its overlay
    author_c = st.container()
    author_col1, _, author_col2, author_col3 = author_c.columns([8, 1, 2, 2])
    author = author_col1.selectbox(
        "Choose the books author to base your recommendations on:",
        st.session_state.authors_cache,
        key="author_selectbox",
    )

    def set_author_filter():
        popular_books = st.session_state.popular_books_cache
        st.session_state.titles_cache = popular_books[
            popular_books["Book-Author"].str.contains(author)
        ]["Book-Title"].unique()

    def clear_author_filter():
        popular_books = st.session_state.popular_books_cache
        st.session_state.titles_cache = popular_books["Book-Title"].unique()

    author_col2.button("Set Author", on_click=set_author_filter)
    author_col3.button("Clear Author", on_click=clear_author_filter)

    def get_rec():
        recs = rec.recommend(title, author)
        if len(recs) > 0:
            st.write("Showing recommendations for:")
            st.write(f"**{title}**, by **{author}**")
            st.write(recs)
        else:
            st.write(
                "Unfortunately, it seemes like there is not enough data for this recommendation."
            )

    st.button("Get recommendations", on_click=get_rec)


if __name__ == "__main__":
    main()
