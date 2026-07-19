from netforge.app.application import NetForgeApplication
from netforge.database.database import initialize_database


def main():
    initialize_database()

    app = NetForgeApplication()
    app.run()


if __name__ == "__main__":
    main()