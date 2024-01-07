import pytest
from sqlalchemy import case, distinct, func, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import aliased

from db import Session
from models import Clazz, Student, StudentClazz, StudentClub


def test_basic_usage():
    """select の基本

    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#using-select-statements
    """  # noqa
    with Session() as session:
        # `select()` は select ステートメントを構築する
        stmt = select(Student.id, Student.name, Student.gender).limit(3)
        print(stmt)
        # => select id, name, gender from students

        # クエリを発行する方法は Core(Non ORM) と ORM で異なる模様
        # Core(Non ORM): `Connection.execute()`
        # ORM          : `Session.execute()`

        # クエリ発行の結果として iteratable な select 要素群が返る
        # (今回の select 要素群は id, name, gender の3つ)
        iterator_result = session.execute(stmt)
        print(f"### {iterator_result}")
        # => `sqlalchemy.engine.result.ChunkedIteratorResult`

        # iteratable なので for で select 要素群を **tuple** で取得できる
        for row in iterator_result:
            print(f"### {row}")
            # => `(Student.id, Student.name, Student.gender)`

            # 1つ目の要素(Student.id)にアクセスする場合はインデックス指定でアクセス
            print(f"### {row[0]}")
            # => `Student.id`


def test_first_all_scalar_scalars():
    """select の結果を取得する方法

    - `first()`
    - `all()`
    - `scalar()`
    - `scalars()`

    ref: https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Result.first
    ref: https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Result.all
    ref: https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Result.scalar
    ref: https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Result.scalars

    NOTE: scalar 系を使う場合は select 要素が一つの場合のみ、と考えて良さそう
    """  # noqa

    # 次のようなレコード群があるとする。
    # [id, name, gender] (header row)
    # [1, "yamada", 1]
    # [2, "sato", 2]
    # [3, "saito", 1]

    with Session() as session:
        stmt = select(Student.id, Student.name, Student.gender).limit(3)

        # `first()` を使うことで1レコード目のみを取得できる
        # (select 要素が tuple で返る)
        id, name, gender = session.execute(stmt).first()
        print(f"### id[{id}] name[{name}] gender[{gender}]")

        # `all()` を使うことで全レコードを取得できる
        # (select 要素が tuple の配列で返る)
        rows = session.execute(stmt).all()
        print(f"### rows[{rows}]")

        # `scalar()` を使うことで1レコード目の1つ目の要素(左上の要素)を取得できる
        # (今回の例では ID:1 が返る)
        id = session.execute(stmt).scalar()
        print(f"### id[{id}]")

        # `scalars()` を使うことで全レコードの1つ目の要素を取得できる
        # (今回の例では ID の配列を持つ ScalarResult オブジェクトが返る)
        ids = session.execute(stmt).scalars()
        print(f"### ids object[{ids}]")
        for id in ids:
            print(f"### id[{id}]")

        # `scalar()` は `scalars()` + `first()` でも実現できる
        # (配列の最初の要素を返すイメージ)
        id = session.execute(stmt).scalars().first()
        print(f"### id[{id}]")

        # `scalars()` では ScalarResult オブジェクトが返るので
        # `all()` を使って tuple の配列に変換できる
        ids = session.execute(stmt).scalars().all()
        print(f"### ids[{ids}]")

        # 以上のことを踏まえると `scalar()` はリテラルな値を返すため `first()` や
        # `all()` が使えないことがわかる
        with pytest.raises(AttributeError) as e:
            session.execute(stmt).scalar().first()
        print(f"### ***ERROR*** [{e}]")
        with pytest.raises(AttributeError) as e:
            session.execute(stmt).scalar().all()
        print(f"### ***ERROR*** [{e}]")


def test_one():
    """first() と似た one()

    ref: https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Result.one

    NOTE: `one()` は1レコードのみであることを保証する。複数行ある場合は MultipleResultsFound の例外
    NOTE: 次のような `one()` 関連のメソッドがある
          - `one_or_none()`
          - `scalar_one()`
          - `scalar_one_or_none()`
    """  # noqa
    with Session() as session:
        stmt = select(Student.id, Student.name, Student.gender).limit(1)
        id, name, gender = session.execute(stmt).one()
        print(f"### id[{id}] name[{name}] gender[{gender}]")

        # 複数行取得した場合
        stmt = select(Student.id, Student.name, Student.gender).limit(3)
        with pytest.raises(MultipleResultsFound) as e:
            session.execute(stmt).one()
        print(f"### ***ERROR*** [{e}]")

        # レコードが存在しない場合
        stmt = select(Student.id, Student.name, Student.gender).where(
            Student.name == "NOT FOUND. NOT FOUND. NOT FOUND."
        )
        with pytest.raises(NoResultFound) as e:
            session.execute(stmt).one()
        print(f"### ***ERROR*** [{e}]")


def test_orderby():
    """
    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#order-by
    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.order_by
    """  # noqa
    with Session() as session:
        stmt = select(Student).order_by(Student.id.desc())
        result = session.execute(stmt)
        students = result.scalars().all()
        for student in students:
            print(f"### student id[{student.id}] name[{student.name}]")


def test_limit_offset():
    """limit, offset (skip, take)

    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.GenerativeSelect.limit
    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.GenerativeSelect.offset
    """  # noqa
    with Session() as session:
        stmt = select(Student).limit(3).offset(10)
        result = session.execute(stmt)
        students = result.scalars().all()
        for student in students:
            print(f"### student id[{student.id}] name[{student.name}]")


def test_count():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/functions.html#sqlalchemy.sql.functions.count
    """  # noqa
    with Session() as session:
        # NOTE: execute を使わずに直接 scalar などを呼べる
        count = session.scalar(select(func.count(StudentClazz.student_id)))
        print(f"### count(StudentClazz.student_id)[{count}]")


def test_count_with_group_by():
    """クラス名と各クラスに所属している生徒数の一覧を出力する

    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#aggregate-functions-with-group-by-having
    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.group_by
    """  # noqa
    with Session() as session:
        stmt = (
            select(Clazz, func.count(StudentClazz.class_id).label("student_num"))
            .join(StudentClazz.clazz)
            .group_by(StudentClazz.class_id)
        )
        result = session.execute(stmt)
        classes = result.all()
        for clazz, student_num in classes:
            print(
                f"### clazz.id[{clazz.id}]"
                f" clazz.name[{clazz.name}]"
                f" student_num[{student_num}]"
            )


def test_count_with_group_by_and_having():
    """所属している生徒数が30以上のクラスのクラス名と生徒数の一覧を出力する

    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#aggregate-functions-with-group-by-having
    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.having
    """  # noqa
    with Session() as session:
        stmt = (
            select(Clazz, func.count(StudentClazz.class_id).label("student_num"))
            .join(StudentClazz.clazz)
            .group_by(StudentClazz.class_id)
            # TODO: label した名称って使えないかね？
            .having(func.count(StudentClazz.class_id) > 30)
        )
        result = session.execute(stmt)
        classes = result.all()
        for clazz, student_num in classes:
            print(
                f"### clazz.id[{clazz.id}]"
                f" clazz.name[{clazz.name}]"
                f" student_num[{student_num}]"
            )


def test_inner_join():
    """生徒の一覧を部活 ID とともに出力する。
    生徒が複数の部活に所属している場合、生徒情報は所属している部活数分を出力する。
    また生徒が部活に所属していない場合は除外する。

    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#tutorial-select-join
    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.join
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#joins
    """  # noqa
    with Session() as session:
        # NOTE: inner join なので club に所属していない生徒は除外する
        stmt = select(Student.id, Student.name, StudentClub.club_id).join(
            StudentClub, StudentClub.student_id == Student.id
        )
        result = session.execute(stmt)
        students = result.all()
        for student in students:
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" student.club_id[{student.club_id}]"
            )
        print(f"### len(student)[{len(students)}]")


def test_outer_join():
    """生徒の一覧を部活 ID とともに出力する。
    生徒が複数の部活に所属している場合、生徒情報は所属している部活数分を出力する。
    また生徒が部活に所属していない場合は部活 ID を None として出力する。

    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#outer-and-full-join
    ref: https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.outerjoin

    NOTE: `RIGHT OUTER JOIN` はないので、使う場合はテーブルの順序を逆にする。 (by tutorial の tips より)
    """  # noqa
    with Session() as session:
        stmt = select(Student.id, Student.name, StudentClub.club_id).outerjoin(
            StudentClub, StudentClub.student_id == Student.id
        )
        result = session.execute(stmt)
        students = result.all()
        for student in students:
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" student.club_id[{student.club_id}]"
            )
        print(f"### len(student)[{len(students)}]")


def test_join_with_subquery():
    """クラス ID 1,3,5 に所属している生徒の一覧を出力する

    ref: https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#tutorial-subqueries-orm-aliased
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#joining-to-subqueries
    """  # noqa
    with Session() as session:
        sub_query = (
            select(StudentClazz.student_id)
            .where(StudentClazz.class_id.in_([1, 3, 5]))
            .subquery()
        )
        stmt = select(Student.id, Student.name).join(
            sub_query, Student.id == sub_query.c.student_id
        )
        result = session.execute(stmt)
        students = result.all()
        for id, name in students:
            print(f"### student.id[{id}]" f" student.name[{name}]")
        print(f"### len(student)[{len(students)}]")


def test_join_with_subquery_and_alias():
    """クラス ID 1,3,5 に所属している生徒の一覧を出力する

    aliased を使って StudentClazz の entity にアクセスする例。
    StudentClazz の student_id や class_id にアクセスできる。
    ただし N+1 問題になるため使いどころは要注意。

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#joining-to-subqueries
    """  # noqa
    with Session() as session:
        sub_query = (
            select(StudentClazz.student_id)
            .where(StudentClazz.class_id.in_([1, 3, 5]))
            .subquery()
        )
        student_class_sub_query = aliased(StudentClazz, sub_query, name="student_class")
        stmt = select(Student.id, Student.name, student_class_sub_query).join(
            student_class_sub_query
        )
        result = session.execute(stmt)
        students = result.all()
        for id, name, student_class in students:
            print(
                f"### student.id[{id}]"
                f" student.name[{name}]"
                f" student_class.student_id[{student_class.student_id}]"
                f" student_class.class_id[{student_class.class_id}]"
            )
        print(f"### len(student)[{len(students)}]")


def test_select_with_subquery():
    """サブクエリの結果を select する

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#selecting-entities-from-subqueries
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#sqlalchemy.orm.aliased
    """  # noqa
    with Session() as session:
        sub_query = select(Student).subquery()
        aliased_student = aliased(Student, sub_query)
        stmt = select(aliased_student)
        result = session.execute(stmt)
        students = result.all()
        for (student,) in students:
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" student.gender[{student.gender}]"
                f" student.address[{student.address}]"
            )
        print(f"### len(student)[{len(students)}]")


def test_distinct():
    """
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.distinct
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.ColumnOperators.distinct
    """  # noqa
    with Session() as session:
        stmt = select(func.count(distinct(StudentClazz.student_id)))
        # ALT: stmt = select(func.count(StudentClazz.student_id.distinct()))
        result = session.execute(stmt)
        count = result.scalar()
        print(f"### count[{count}]")


def test_case():
    """case 句を使って男女の人数をカウントする

    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.case
    ref: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.Case
    """  # noqa
    with Session() as session:
        stmt = select(
            func.sum(case((Student.gender == 1, 1), else_=0)),
            func.sum(case((Student.gender == 2, 1), else_=0)),
        )
        result = session.execute(stmt)
        man_count, woman_count = result.first()
        print(f"### man_count[{man_count}] woman_count[{woman_count}]")


def test_server_side_cursors():
    """結果を分割して処理する。(メモリのバッファオーバーフロー対策)

    `chunk` などと呼ばれる仕組み。

    ref: https://docs.sqlalchemy.org/en/20/core/connections.html#using-server-side-cursors-a-k-a-stream-results

    NOTE: `Result.all()` を使うと指定取得数を無視してすべてのレコードをフェッチする点に注意、とのこと。
    TODO: クエリ的には１回しか呼ばれてない。 DB 側でバッファリングしてる？
    """  # noqa
    with Session() as session:
        stmt = select(Student)
        cursor = session.execute(stmt, execution_options={"yield_per": 50})
        for students in cursor.partitions():
            for (student,) in students:
                print(f"### student id[{student.id}] name[{student.name}]")


def test_server_side_cursors_alt_ver2():
    """結果を分割して処理する。(メモリのバッファオーバーフロー対策) (ORM)

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#fetching-large-result-sets-with-yield-per

    NOTE: `yield_per` は eager ロードと互換性がないらしいので注意が必要、とのこと。
    """  # noqa
    with Session() as session:
        stmt = select(Student).execution_options(yield_per=50)
        cursor = session.scalars(stmt).partitions()
        for students in cursor:
            for student in students:
                print(f"### student id[{student.id}] name[{student.name}]")


def test_server_side_cursors_alt_ver3():
    """結果を分割して処理する。(メモリのバッファオーバーフロー対策) (ORM) (Alt Ver)

    cursor を隠蔽するケース。

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#fetching-large-result-sets-with-yield-per
    """  # noqa
    with Session() as session:
        stmt = select(Student).execution_options(yield_per=50)
        students = session.scalars(stmt)
        for student in students:
            print(f"### student id[{student.id}] name[{student.name}]")
