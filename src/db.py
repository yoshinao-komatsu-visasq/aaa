"""DB 接続用の conf

ここの Session を使って DB に接続します。

ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#what-does-the-session-do
ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker
ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
"""  # noqa

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

url = URL.create(
    drivername="mysql+pymysql",
    username="testuser",
    password="testpassword",
    host="localhost",
    database="testdb",
    port=3306,
)
engine = create_engine(url, echo=True)
Session = sessionmaker(bind=engine)


def test_db_connecting():
    with Session() as session:
        session.execute(text("select 1"))
        session.commit()
