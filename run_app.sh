#!/usr/bin/env sh

#python3.8 -m pip install -r etl-requirements.txt
#python3.8 etl.py

if [ ! -f "books_ratings.db" ]; then
  echo "Error: SQLite db file is required before running the app container."
  echo "Please try to run the etl.py script first."
  exit 1
fi
echo "SQLite books_ratings.db found."
echo ""

bookRatingsDB="books_ratings.db"

docker run --rm -d \
    -p 8501:8501 \
    -v `pwd`/$bookRatingsDB:/app/$bookRatingsDB:ro \
    datasentics-de-task
