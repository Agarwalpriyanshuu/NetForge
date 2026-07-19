from sqlalchemy.orm import Session

from netforge.database.database import SessionLocal
from netforge.models.connection import Connection


class ConnectionService:

    def create_connection(self, data):

        db: Session = SessionLocal()

        connection = Connection(
            name=data["name"],
            hostname=data["hostname"],
            ip_address=data["ip"],
            username=data["username"],
            password=data["password"],
            protocol=data["protocol"],
            port=int(data["port"]),
            notes=data["notes"],
        )

        db.add(connection)
        db.commit()
        db.close()

    def delete(self, connection_id):

        db = SessionLocal()

        connection = db.get(Connection, connection_id)

        if connection:
            db.delete(connection)
            db.commit()

        db.close()

    def update(self, connection_id, data):

        db = SessionLocal()

        connection = db.get(Connection, connection_id)

        if connection is None:
            db.close()
            return

        connection.name = data["name"]
        connection.hostname = data["hostname"]
        connection.ip_address = data["ip"]
        connection.username = data["username"]
        connection.password = data["password"]
        connection.protocol = data["protocol"]
        connection.port = int(data["port"])
        connection.notes = data["notes"]

        db.commit()

        db.close()

    def get_all(self):

        db: Session = SessionLocal()

        data = db.query(Connection).all()

        db.close()

        return data