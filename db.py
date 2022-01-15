import sqlite3
from pathlib import Path

query = dict()
query["notices"] = """
CREATE TABLE IF NOT EXISTS notices (
    no integer not null primary key,
    title text not null,
    author integer not null,
    content text not null,
    published datetime not null,
    attached text
)"""
query["special_posts"] = """
CREATE TABLE IF NOT EXISTS special_posts (
    title text not null unique,
    content text not null,
    author integer not null,
    published datetime not null,
    attached text
);
"""
query["users"] = """
CREATE TABLE IF NOT EXISTS users (
    id integer not null primary key,
    username text not null,
    password text not null,
    role text not null
)
"""

def initalize():
    global query
    Path("sql").mkdir(exist_ok=True)
    for name, query in query.items():
        with sqlite3.connect(f"sql/{name}.db") as DB:
            DB.execute(query)