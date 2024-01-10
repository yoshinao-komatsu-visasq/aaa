"""DB 接続用の conf

ここの Session を使って DB に接続します。

ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#what-does-the-session-do
ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker
ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
"""  # noqa

import os

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USERNAME", "testuser"),
    password=os.getenv("DB_PASSWORD", "testpassword"),
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_DATABASE", "testdb"),
    port=int(os.getenv("DB_PORT", "3306")),
)
print(f"### db conn url[{url}]")

engine = create_engine(url, echo=True)
Session = sessionmaker(bind=engine)


def test_db_connecting():
    with Session() as session:
        session.execute(text("select 1"))
        session.commit()
