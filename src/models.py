"""ORM 用のモデル

ref: https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html
"""  # noqa
from datetime import datetime

from sqlalchemy import INTEGER, ForeignKey, String, func
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Student(Base):
    """
    - Email に対しては one-to-many
    - StudentClazz に対しては one-to-one

    ref: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#one-to-many
    ref: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#one-to-one
    ref: https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship
    ref: https://docs.sqlalchemy.org/en/20/orm/collection_api.html#customizing-collection-access

    NOTE: `relationship()` の `back_populates` では、リレーション先に存在する attribute を指定する。存在しない場合はエラーとなる
    """  # noqa

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # TODO: enum とかで表したい
    gender: Mapped[int] = mapped_column(INTEGER, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[int] = mapped_column(INTEGER, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    emails: Mapped[list["Email"]] = relationship(back_populates="student")
    # Classic Style: emails = relationship("Email", collection_class=set, back_populates="student")  # noqa

    clazz: Mapped["StudentClazz"] = relationship()
    # NOTE: Imperative な場合に one-to-one 制約を付与する場合は
    #       親側の relationship に `uselist=False` を付与する
    # Classic Style: clazz = relationship("Clazz", uselist=False, back_populates="student")  # noqa

    # 楽観的ロックの検証用。システム的に updated_at を更新するため version_id_generator は False となる
    __mapper_args__ = {"version_id_col": updated_at, "version_id_generator": False}


class Email(Base):
    __tablename__ = "emails"

    # TODO: mail 用の型とかある？
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    student_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("students.id", ondelete="CASCADE")
    )

    # NOTE: 複合主キー
    # ref: https://docs.sqlalchemy.org/en/20/orm/declarative_config.html#mapper-configuration-options-with-declarative  # noqa
    __mapper_args__ = {"primary_key": [email, student_id]}

    # 検証用に back_populates は指定していない
    student: Mapped["Student"] = relationship()


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Clazz(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Club(Base):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    teacher_id: Mapped[int] = mapped_column(INTEGER, nullable=True)


class StudentClazz(Base):
    """
    - Student に対して one-to-one
    - Clazz に対して one-to-one

    ref: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#declarative-table-configuration
    ref: https://docs.sqlalchemy.org/en/20/core/constraints.html#sqlalchemy.schema.UniqueConstraint
    """  # noqa

    __tablename__ = "student_clazz"

    student_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    class_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("classes.id", ondelete="RESTRICT")
    )

    student: Mapped["Student"] = relationship(back_populates="clazz")
    clazz: Mapped["Clazz"] = relationship()


class TeacherClazz(Base):
    __tablename__ = "teacher_clazz"

    teacher_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("teachers.id", ondelete="RESTRICT")
    )
    class_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("classes.id", ondelete="CASCADE")
    )

    __mapper_args__ = {"primary_key": [teacher_id, class_id]}


class StudentClub(Base):
    __tablename__ = "student_club"

    student_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("students.id", ondelete="CASCADE")
    )
    club_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("clubs.id", ondelete="RESTRICT")
    )

    __mapper_args__ = {"primary_key": [student_id, club_id]}
