from sqlalchemy import and_, between, func, not_, null, or_, select

from db import Session
from models import Student, StudentClazz
from models_club import Club, StudentClub


def test_logical_groping():
    """
    NOTE: and や or の中で and や or をネストして宣言すると論理グループとして処理する
    """
    with Session() as session:
        stmt = select(func.count(Student.id)).where(
            and_(Student.id == 1, or_(Student.id == 2, Student.id == 3))
        )
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_and():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.and_

    NOTE: and はカンマ区切りでOK.
    """  # noqa
    with Session() as session:
        stmt = select(func.count(Student.id)).where(
            Student.id == 2, Student.name.ilike("s%")
        )
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_or():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.or_
    """  # noqa
    with Session() as session:
        stmt = select(func.count(Student.id)).where(
            or_(Student.name.ilike("%山田%"), Student.name.ilike("%佐藤%"))
        )
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_not():
    """クラス ID:1 に所属している人数と所属していない人数を出力する

    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.or_
    """  # noqa
    with Session() as session:
        member_count = session.execute(
            select(func.count(StudentClazz.student_id)).where(
                StudentClazz.class_id == 1
            )
        ).scalar()

        non_member_count = session.execute(
            select(func.count(StudentClazz.student_id)).where(
                not_(StudentClazz.class_id == 1)
            )
        ).scalar()

        print(f"### member_count[{member_count}] non_member_count[{non_member_count}]")


def test_in():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.ColumnOperators.in_

    NOTE: 否定の `not_in()` や `notin_()` がある。
    """  # noqa
    with Session() as session:
        stmt = select(func.count(StudentClazz.student_id)).where(
            StudentClazz.class_id.in_([1, 2, 3])
        )
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_like():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.ColumnOperators.like

    NOTE: 次のような like 関連のメソッドがある
          - 否定: `notlike()`, `not_like()`
          - 大文字小文字を無視: `ilike()`
          - 否定で大文字小文字を無視: `notilike()`, `not_ilike()`
    """  # noqa
    with Session() as session:
        stmt = select(func.count(Student.id)).where(Student.name.like("%佐藤%"))
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_between():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.between
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.ColumnOperators.between
    """  # noqa
    with Session() as session:
        stmt = select(func.count(Student.id)).where(between(Student.id, 1, 5))
        # ALT: stmt = select(func.count(Student.id)).where(Student.id.between(1, 5))
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_exists():
    """部活に所属している生徒の数を出力する

    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#exists-subqueries
    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.exists
    """  # noqa
    with Session() as session:
        stmt = select(func.count(Student.id)).where(
            (select(1).where(Student.id == StudentClub.student_id)).exists()
        )
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_null():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.null
    """  # noqa
    with Session() as session:
        stmt = select(Club).where(Club.teacher_id == null())
        result = session.execute(stmt)
        clubs = result.all()
        for (club,) in clubs:
            print(f"### club.id[{club.id}] club.name[{club.name}]")


def test_subquery():
    """
    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#tutorial-subqueries-orm-aliased
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#selecting-entities-from-subqueries
    """  # noqa
    with Session() as session:
        stmt = select(Club).where(Club.teacher_id == null())
        result = session.execute(stmt)
        clubs = result.all()
        for (club,) in clubs:
            print(f"### club.id[{club.id}] club.name[{club.name}]")
