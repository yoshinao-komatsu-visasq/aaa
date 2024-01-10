"""検証用データ投入用 seeder"""

import random

from faker import Faker
from sqlalchemy import insert, select

from db import Session, engine
from models import Base, Clazz, Email, Student, StudentClazz, Teacher, TeacherClazz
from models_club import Club, StudentClub

faker = Faker(["ja-JP"])


def add_teachers():
    names = [{"name": f"T{faker.name()}"} for _ in range(30)]
    stmt = insert(Teacher).values(names)
    with Session() as session:
        session.execute(stmt)
        session.commit()


def add_class():
    names = [{"name": f"C{faker.unique.town()}"} for _ in range(10)]
    stmt = insert(Clazz).values(names)
    with Session() as session:
        session.execute(stmt)
        session.commit()


def add_club():
    # TODO: 手直ししたい
    stmt = insert(Club).values(
        [
            {"name": "C野球部", "teacher_id": 1},
            {"name": "Cサッカー部", "teacher_id": 2},
            {"name": "Cバスケットボール部", "teacher_id": 3},
            {"name": "C陸上部", "teacher_id": 4},
            {"name": "Cバレーボール部", "teacher_id": 5},
            {"name": "Cテニス部", "teacher_id": 6},
            {"name": "C硬式テニス部", "teacher_id": 7},
            {"name": "Cバドミントン部", "teacher_id": 8},
            {"name": "C吹奏楽部", "teacher_id": 9},
            {"name": "C美術部", "teacher_id": None},
        ]
    )
    with Session() as session:
        session.execute(stmt)
        session.commit()


def add_students():
    students = []
    for _ in range(300):
        gender = faker.pyint(min_value=1, max_value=2)
        students.append(
            {
                "name": f"S{faker.name_male()}"
                if gender == 1
                else f"S{faker.name_female()}",
                "gender": gender,
                "address": faker.address(),
                "score": faker.pyint(min_value=0, max_value=100),
            }
        )
    stmt = insert(Student).values(students)
    with Session() as session:
        session.execute(stmt)
        session.commit()


def add_email():
    with Session() as session:
        result = session.execute(select(Student.id))
        student_ids = result.scalars().all()

    email_list = []
    for student_id in student_ids:
        count = faker.pyint(min_value=1, max_value=3)
        for _ in range(count):
            email_list.append({"email": faker.email(), "student_id": student_id})

    stmt = insert(Email).values(email_list)
    with Session() as session:
        session.execute(stmt)
        session.commit()


def add_teacher_class():
    with Session() as session:
        result = session.execute(select(Clazz.id))
        class_ids = result.scalars().all()
        result = session.execute(select(Teacher.id))
        teacher_ids = result.scalars().all()

    teacher_class = []
    for class_id in class_ids:
        pickup_teacher_ids = random.sample(
            teacher_ids, faker.pyint(min_value=1, max_value=3)
        )
        for teacher_id in pickup_teacher_ids:
            teacher_class.append({"teacher_id": teacher_id, "class_id": class_id})

    stmt = insert(TeacherClazz).values(teacher_class)
    with Session() as session:
        session.execute(stmt)
        session.commit()


def add_student_class():
    with Session() as session:
        result = session.execute(select(Clazz.id))
        class_ids = result.scalars().all()
        result = session.execute(select(Student.id))
        student_ids = result.scalars().all()

    student_class = []
    for student_id in student_ids:
        pickup_class_id = random.choice(class_ids)
        student_class.append({"student_id": student_id, "class_id": pickup_class_id})

    stmt = insert(StudentClazz).values(student_class)
    with Session() as session:
        session.execute(stmt)
        session.commit()


def add_student_club():
    with Session() as session:
        result = session.execute(select(Club.id))
        club_ids = result.scalars().all()
        result = session.execute(select(Student.id))
        student_ids = result.scalars().all()

    student_club = []
    for student_id in student_ids:
        club_count = faker.pyint(min_value=0, max_value=2)
        pickup_club_ids = random.sample(club_ids, club_count)
        for club_id in pickup_club_ids:
            student_club.append({"student_id": student_id, "club_id": club_id})

    stmt = insert(StudentClub).values(student_club)
    with Session() as session:
        session.execute(stmt)
        session.commit()


def test_seeder():
    """
    ref: https://docs.sqlalchemy.org/en/20/orm/quickstart.html#emit-create-table-ddl
    ref: https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.MetaData.create_all
    """  # noqa
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    add_teachers()
    add_class()
    add_club()
    add_students()
    add_email()
    add_teacher_class()
    add_student_class()
    add_student_club()
