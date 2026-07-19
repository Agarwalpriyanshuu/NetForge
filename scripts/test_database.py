from services.connection_service import ConnectionService

service = ConnectionService()

service.create_connection(
    name="Production",
    hostname="prod.company.com",
    ip_address="10.10.10.5",
    username="admin",
    port=22,
)

print("Saved")

for connection in service.get_connections():

    print(
        connection.id,
        connection.name,
        connection.ip_address,
        connection.port,
    )