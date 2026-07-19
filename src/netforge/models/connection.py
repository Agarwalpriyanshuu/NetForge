from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from netforge.database.base import Base


class Connection(Base):

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(String(100))

    hostname: Mapped[str] = mapped_column(String(255))

    ip_address: Mapped[str] = mapped_column(String(50))

    username: Mapped[str] = mapped_column(String(100))

    password: Mapped[str] = mapped_column(
        String(255),
        default=""
    )

    protocol: Mapped[str] = mapped_column(
        String(20),
        default="SSH"
    )

    port: Mapped[int] = mapped_column(Integer)

    notes: Mapped[str] = mapped_column(
        String(1000),
        default=""
    )

    tags: Mapped[str] = mapped_column(
        String(255),
        default=""
    )

    favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )