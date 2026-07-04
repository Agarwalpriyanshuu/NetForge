from netforge.database.database import SessionLocal
from netforge.models.connection import Connection


class ConnectionService:

    def create_connection(
        self,
        name,
        hostname,
        ip_address,
        username,
        port,
        description="",
        tags="",
        favorite=False,
    ):

        session = SessionLocal()

        try:

            connection = Connection(
                name=name,
                hostname=hostname,
                ip_address=ip_address,
                username=username,
                port=port,
                description=description,
                tags=tags,
                favorite=favorite,
            )

            session.add(connection)

            session.commit()

            session.refresh(connection)

            return connection

        finally:
            session.close()

    def get_connections(self):

        session = SessionLocal()

        try:

            return session.query(Connection).all()

        finally:
            session.close()

    def delete_connection(self, connection_id):

        session = SessionLocal()

        try:

            connection = session.get(Connection, connection_id)

            if connection:

                session.delete(connection)

                session.commit()

        finally:
            session.close()