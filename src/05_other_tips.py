import threading
import time

import pytest
from sqlalchemy import bindparam, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.exc import StaleDataError

import models_club  # noqa
from db import Session
from models import Student


def test_upsert():
    """
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-upsert-statements
    ref: https://docs.sqlalchemy.org/en/20/dialects/mysql.html#insert-on-duplicate-key-update-upsert (ONLY MySQL)
    """  # noqa
    with Session() as session:
        stmt = (
            insert(Student)
            .values(id=1, name="name", gender=1, address="address", score=50)
            .on_duplicate_key_update(
                name="name name name",
            )
        )
        session.execute(stmt)
        session.commit()


def test_bulk_insert():
    with Session() as session:
        students = [
            {
                "name": "name1",
                "gender": 1,
                "address": "address1",
                "score": 33,
            },
            {
                "name": "name2",
                "gender": 2,
                "address": "address2",
                "score": 66,
            },
            {
                "name": "name3",
                "gender": 1,
                "address": "address3",
                "score": 99,
            },
        ]
        stmt = insert(Student).values(
            name=bindparam("name"),
            gender=bindparam("gender"),
            address=bindparam("address"),
        )
        session.execute(stmt, students)
        session.commit()


def test_session_明示的なbegin_commit_rollback():
    """
    ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block
    """  # noqa
    with Session() as session:
        session.begin()
        try:
            ...
        except:  # noqa
            session.rollback()
            raise
        else:
            session.commit()


def test_session_自動commit():
    """
    ref: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block
    """  # noqa
    with Session() as session:
        # ここは session scope (?)
        with session.begin():
            # ここは transaction scope (?)
            ...
        # 例外がなければ自動的に commit, 例外があれば自動的に rollback?

    # 直接 begin も呼べる
    with Session.begin() as session:
        ...


def test_pessimistic_lock():
    """悲観的ロック

    ref: https://blog.amedama.jp/entry/2015/09/28/065805
    ref: https://qiita.com/t_okkan/items/ce9d145750cd07e70606
    """  # noqa

    def _update(thread_key, student_id, score, wait):
        with Session() as session:
            # 悲観的ロックの場合は後続が select の発行で待ちとなる
            student = session.scalar(
                select(Student).where(Student.id == student_id).with_for_update()
            )
            print(f"### [{thread_key}] student.score[{student.score}]")

            print(f"### [{thread_key}] Sleep[{wait}]")
            time.sleep(wait)
            print(f"### [{thread_key}] Wake Up!")

            student.score += score
            student_score = student.score

            session.commit()

            print(f"### [{thread_key}] Finish! student.score[{student_score}]")

    t1 = threading.Thread(target=_update, args=("t1", 1, 1, 1))
    t2 = threading.Thread(target=_update, args=("t2", 1, 1, 1))
    # もちろんロックしていないユーザーは待たされない
    t3 = threading.Thread(target=_update, args=("t3", 2, 1, 1))
    t1.start()
    t2.start()
    t3.start()


def test_pessimistic_lock_to_table():
    """テーブルに対する悲観的ロック"""

    def _update(thread_key, session, student, score, wait):
        print(f"### [{thread_key}] student.score[{student.score}]")

        print(f"### [{thread_key}] Sleep[{wait}]")
        time.sleep(wait)
        print(f"### [{thread_key}] Wake Up!")

        student.score += score
        student_score = student.score

        session.commit()

        print(f"### [{thread_key}] Finish! student.score[{student_score}]")

    def _update_with_row_lock(thread_key, student_id, score, wait):
        with Session() as session:
            # 後発にしたいので 0.1s スリープ
            time.sleep(0.1)
            student = session.scalar(
                select(Student).where(Student.id == student_id).with_for_update()
            )
            _update(thread_key, session, student, score, wait)

    def _update_with_table_lock(thread_key, score, wait):
        with Session() as session:
            student = session.scalar(
                select(Student).order_by(Student.id.asc()).with_for_update()
            )
            _update(thread_key, session, student, score, wait)

    t1 = threading.Thread(target=_update_with_table_lock, args=("t1", 1, 1))
    t2 = threading.Thread(target=_update_with_table_lock, args=("t2", 1, 1))
    # テーブルロックの場合は t3 も待ちとなる
    t3 = threading.Thread(target=_update_with_row_lock, args=("t3", 2, 1, 1))
    t1.start()
    t2.start()
    t3.start()


def test_optimistic_lock():
    """楽観的ロック

    ref: https://blog.amedama.jp/entry/2015/09/28/065805
    ref: https://qiita.com/t_okkan/items/ce9d145750cd07e70606
    ref: https://docs.sqlalchemy.org/en/20/orm/versioning.html
    ref: models.py::Student
    """  # noqa

    def _update(thread_key, student_id, score, wait):
        with Session() as session:
            student = session.scalar(select(Student).where(Student.id == student_id))

            print(f"### [{thread_key}] Sleep[{wait}]")
            time.sleep(wait)
            print(f"### [{thread_key}] Wake Up!")

            student.score += score

            try:
                session.commit()
            except StaleDataError as e:
                print(f"### [{thread_key}] ***ERROR*** [{e}]")

            print(f"### [{thread_key}] Finish!")

    # t1 が先行して UPDATE するため、後続の t2 は version_id_col で監視している updated_at が
    # アンマッチとなり StaleDataError の例外が発生する。
    t1 = threading.Thread(target=_update, args=("t1", 1, 1, 0))
    t2 = threading.Thread(target=_update, args=("t2", 1, 1, 0.5))
    t1.start()
    t2.start()


def test_テストスイート向けのsavepointを利用したコミットのロールバック():
    """
    ref: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

    TODO: コミットのロールバックってなんやねん
    """  # noqa
    from db import engine

    connection = engine.connect()
    transaction = connection.begin()
    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        student = Student(name="name", gender=1, address="address", score=50)
        session.add(student)
        session.commit()
        student_id = student.id
        print(f"### student.id[{student.id}]")
    transaction.rollback()
    connection.close()

    # ロールバックによりコミットした student が存在しない
    with Session() as session:
        with pytest.raises(NoResultFound) as e:
            student = session.execute(
                select(Student).where(Student.id == student_id)
            ).one()
        print(f"### ***ERROR*** [{e}]")
