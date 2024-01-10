"""部活に関するモデル群

循環インポート検証用に別ファイルとした。
"""  # noqa

from sqlalchemy import INTEGER, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base, Student


class Club(Base):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    teacher_id: Mapped[int] = mapped_column(INTEGER, nullable=True)


class StudentClub(Base):
    """
    - Student に対しては many-to-one
    """

    __tablename__ = "student_club"

    student_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("students.id", ondelete="CASCADE")
    )
    club_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("clubs.id", ondelete="RESTRICT")
    )

    student: Mapped["Student"] = relationship()

    __mapper_args__ = {"primary_key": [student_id, club_id]}
