"""relationships に関する tips

ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#relationship-loading-techniques
"""  # noqa
import pytest
from sqlalchemy import select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Load, contains_eager, joinedload, raiseload, selectinload
from sqlalchemy.orm.exc import DetachedInstanceError

from db import Session
from models import Clazz, Email, Student, StudentClazz


def test_basic_relationship():
    with Session() as session:
        student1 = Student(name="name", gender=1, address="address", score=50)

        # Student モデルに emails のリレーションを宣言しているのでアクセスできる (現状は空配列)
        print(f"### student1.emails[{student1.emails}]")

        # もちろん追加できる
        email1 = Email(email="username1@example.com")
        student1.emails.append(email1)
        print(f"### student1.emails[{student1.emails}]")

        # モデルで次のように宣言しているため、追加すると逆アクセスもできるようになる
        # - Student モデルに emails のリレーションを宣言、および back_populates で依存先の属性(`student`)を宣言している
        # - Email モデルに student のリレーションを宣言している
        print(f"### email1.student[{email1.student}]")

        # お試しとして Email モデルでは back_populates を宣言していないため、
        # Email 側で追加しても逆アクセスはできない
        email2 = Email(email="username2@example.com")
        print(f"### email2.student[{email2.student}]")
        email2.student = student1
        print(f"### email2.student[{email2.student}]")
        print(f"### student1.emails[{student1.emails}]")  # email2 が追加されていない

        print(f"### student1.id[{student1.id}]")  # ここでは id は None

        session.add(student1)
        print(f"### student1 in session[{student1 in session}]")
        print(f"### email1 in session[{email1 in session}]")
        print(f"### email2 in session[{email2 in session}]")
        session.commit()
        # => student1 と email1 はコミットするが email2 はコミットしない

        # commit するとオブジェクトをリフレッシュするため、オブジェクトの attribute にアクセスすると
        # select クエリを発行して id を含めて再取得する
        print(f"### student1.id[{student1.id}]")

        # emails にもアクセスできるが遅延ロードとなる(アクセス時にクエリを発行する)
        print(f"### student1.emails[{student1.emails}]")


def test_detached_instance_error():
    """コミット後に session 外でアクセスすると DetachedInstanceError となる

    このため session 外でアクセスする場合には事前に session 内でアクセスしておくと良い。
    """
    with Session() as session:
        student = Student(name="name", gender=1, address="address", score=50)
        session.add(student)
        session.commit()
    with pytest.raises(DetachedInstanceError) as e:
        print(f"### student1.id[{student.id}]")
    print(f"### ***ERROR*** [{e}]")


def test_join_by_relationship():
    """
    ref: https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html#using-relationships-to-join
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#simple-relationship-joins

    NOTE: join にリレーションを指定すると、自動的に外部キーで join してくれる
    TODO: 外部キーがない場合はエラーになるのか？
    """  # noqa
    with Session() as session:
        stmt = select(Student, StudentClazz).join(Student.clazz)
        result = session.execute(stmt)
        students = result.all()
        for record in students:
            # record が tuple なのでモデル名でアクセスできる
            print(
                f"### student.id[{record.Student.id}]"
                f" student.name[{record.Student.name}]"
                f" student_clazz.class_id[{record.StudentClazz.class_id}]"
            )

        # tuple が返るので展開して受け取ることもできる
        for student, student_clazz in students:
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" student_clazz.class_id[{student_clazz.class_id}]"
            )


def test_multi_join_by_relationship():
    """
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#chaining-multiple-joins
    """  # noqa
    with Session() as session:
        stmt = select(Student, Clazz).join(Student.clazz).join(StudentClazz.clazz)
        result = session.execute(stmt)
        students = result.all()
        for student, clazz in students:
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" clazz.id[{clazz.id}]"
                f" clazz.name[{clazz.name}]"
            )


def test_lazy_load():
    """joinやeagerロードを使わずに複数回のクエリを発行するケース

    ローディングのデフォルト。

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#lazy-loading

    NOTE: `student.clazz.class_id` を取得する際に select 文を毎度発行するため N+1 問題となるケース
    """  # noqa
    with Session() as session:
        stmt = select(Student).limit(3)
        result = session.execute(stmt)
        students = result.scalars().all()
        for student in students:
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" student.clazz.class_id[{student.clazz.class_id}]"
            )


def test_selectin_load():
    """リレーション先を in 句で eager ロードする

    次の2つの select を発行する。

    - リレーション元の select
    - リレーション元の ID を in 句にしたリレーション先の select

    一対多、多対多では selectin load を推奨している。

    ref: https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html#selectin-load
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#select-in-loading
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#what-kind-of-loading-to-use
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#sqlalchemy.orm.selectinload

    NOTE: いくつかの制約あり。
          - in 句を使うため上限制約を考慮する必要がある
          - 複合主キーについては DB 依存
    """  # noqa
    with Session() as session:
        stmt = select(Student).options(selectinload(Student.emails)).limit(3)
        result = session.execute(stmt)
        for student in result.scalars():
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" student.emails[{[email.email for email in student.emails]}]"
            )


def test_joined_load_with_many_to_one_relationship():
    """多対一のリレーションに対する joined load による eager ロード

    join によるロードのためクエリを1回発行する。

    これは Email(多側) が基準のケース。

    多対一 では joined load を推奨している。

    ref: https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html#joined-load
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#what-kind-of-loading-to-use
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#sqlalchemy.orm.joinedload
    """  # noqa
    with Session() as session:
        stmt = (
            select(Email).options(joinedload(Email.student, innerjoin=False)).limit(3)
        )
        result = session.execute(stmt)
        for email in result.scalars().all():
            print(
                f"### student.id[{email.student.id}]"
                f" student.name[{email.student.name}]"
                f" student.emails[{email.email}]"
            )


def test_joined_load_with_one_to_many_relationship():
    """一対多のリレーションに対する joined load による eager ロード

    これは Student(一側) が基準のケース。

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading

    NOTE: 一対多の関係を joined load する場合は `unique()` する必要がある。 (by queryguide の tips より)
          理由は join で結合するため一側が複数行となるため。
          `unique()` がないと `sqlalchemy.exc.InvalidRequestError` の例外となる
    """  # noqa
    with Session() as session:
        stmt = (
            select(Student)
            .options(joinedload(Student.emails, innerjoin=False))
            .limit(3)
        )
        result = session.execute(stmt)
        for student in result.scalars().unique().all():
            print(
                f"### student.id[{student.id}]"
                f" student.name[{student.name}]"
                f" student.emails[{[email.email for email in student.emails]}]"
            )

        # `unique()` がない場合
        result = session.execute(stmt)
        with pytest.raises(InvalidRequestError) as e:
            result.scalars().all()
        print(f"### ***ERROR*** [{e}]")


def test_contains_eager():
    """join した結果を流用した eager ロード

    ref: https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html#explicit-join-eager-load
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#routing-explicit-joins-statements-into-eagerly-loaded-collections

    NOTE: join の際に `options(contains_eager(xxx))` の宣言がない場合、バッファリングされていない student が必要な際に
          select のクエリを発行するため N+1 問題となり得る。
    TODO: リレーション先をフィルタリングしたい場合などは contains_eager を使う感じ？
    """  # noqa
    with Session() as session:
        stmt = (
            select(Email)
            .join(Email.student)
            .options(contains_eager(Email.student))
            .limit(3)
        )
        result = session.execute(stmt)
        for email in result.scalars().all():
            print(
                f"### student.id[{email.student.id}]"
                f" student.name[{email.student.name}]"
                f" student.emails[{email.email}]"
            )


def test_raiseload():
    """N+1 問題は絶対にゆるさんぞい

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#preventing-unwanted-lazy-loads-using-raiseload
    """  # noqa
    with Session() as session:
        stmt = select(Student).options(joinedload(Student.clazz), raiseload("*"))
        result = session.execute(stmt)
        student = result.scalars().first()
        print(f"### student.id[{student.id}]")
        print(f"### student.name[{student.name}]")

        # Student -> StudentClazz は joinedload しているので OK
        print(f"### student.class[{student.clazz}]")

        # Student -> StudentClazz -> Clazz は OUT
        with pytest.raises(InvalidRequestError) as e:
            print(f"### student.class.class[{student.clazz.clazz}]")
        print(f"### ***ERROR*** [{e}]")

        # Student -> Email は OUT
        with pytest.raises(InvalidRequestError) as e:
            print(f"### student.email[{student.emails}]")
        print(f"### ***ERROR*** [{e}]")


def test_raiseload_特定の遅延ロード禁止を設定する():
    with Session() as session:
        # Student -> StudentClazz -> Clazz は OK
        # Student -> Email は OUT
        stmt = (
            select(Student)
            .options(joinedload(Student.clazz), Load(Student).raiseload("*"))
            .limit(1)
        )
        result = session.execute(stmt)
        student = result.scalars().first()
        print(f"### student.class.class[{student.clazz.clazz}]")
        with pytest.raises(InvalidRequestError) as e:
            print(f"### student.email[{student.emails}]")
        print(f"### ***ERROR*** [{e}]")

    # Student に対する select の設定をクリアするために session を再発行
    with Session() as session:
        # Student -> StudentClazz -> Clazz は OUT
        # Student -> Email は OK
        stmt = (
            select(Student).options(joinedload(Student.clazz).raiseload("*")).limit(1)
        )
        result = session.execute(stmt)
        student = result.scalars().first()
        print(f"### student.email[{student.emails}]")
        with pytest.raises(InvalidRequestError) as e:
            print(f"### student.class.class[{student.clazz.clazz}]")
        print(f"### ***ERROR*** [{e}]")


def test_multi_joinedload():
    """
    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#joined-eager-loading
    """  # noqa
    with Session() as session:
        stmt = select(Student).options(
            joinedload(Student.emails, innerjoin=False),
            joinedload(Student.clazz, innerjoin=False),
        )
        result = session.execute(stmt)
        student = result.scalar()
        print(f"### student.id[{student.id}]")
        print(f"### student.name[{student.name}]")
        print(f"### student.emails[{[email.email for email in student.emails]}]")
        print(f"### student.clazz.class_id[{student.clazz.class_id}]")


def test_eager_loading_specific_columns():
    """特定カラムの eager load

    ref: https://docs.sqlalchemy.org/en/20/orm/queryguide/columns.html#using-load-only-on-related-objects-and-collections
    """  # noqa
    with Session() as session:
        stmt = select(StudentClazz).options(
            # raiseload を付与して name 以外の lazy load を禁止する
            joinedload(StudentClazz.student).load_only(Student.name, raiseload=True)
        )
        result = session.execute(stmt)
        student_clazz = result.scalar()
        print(f"### student_clazz.class_id[{student_clazz.class_id}]")
        print(f"### student_clazz.student_id[{student_clazz.student_id}]")
        print(f"### student_clazz.student.id[{student_clazz.student.id}]")
        print(f"### student_clazz.student.name[{student_clazz.student.name}]")
        with pytest.raises(InvalidRequestError) as e:
            print(f"### student_clazz.student.address[{student_clazz.student.address}]")
        print(f"### ***ERROR*** [{e}]")
