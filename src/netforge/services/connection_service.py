from sqlalchemy.orm import Session

from netforge.core.security import credential_vault
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
            password=credential_vault.encrypt(data["password"]),
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
        connection.password = credential_vault.encrypt(data["password"])
        connection.protocol = data["protocol"]
        connection.port = int(data["port"])
        connection.notes = data["notes"]

        db.commit()

        db.close()

    def get_all(self):

        db: Session = SessionLocal()

        data = db.query(Connection).all()

        db.close()

        # Decrypt in place: callers (Inventory dialogs, the SSH
        # controller, ...) work with plaintext passwords in memory,
        # exactly as before this feature existed. Only the on-disk
        # representation is encrypted. These objects are already
        # detached from the session (db.close() happened above), so
        # mutating .password here does not risk an unexpected write
        # back to the database.
        for connection in data:
            connection.password = credential_vault.decrypt(connection.password)

        return data