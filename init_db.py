import sqlite3

DEFAULT_DB_FILE = 'parking_system.db'

def initialize_database(db_filename=DEFAULT_DB_FILE):
    connection = sqlite3.connect(db_filename)
    cursor = connection.cursor()

    cursor.execute('DROP TABLE IF EXISTS Bookings')
    cursor.execute('DROP TABLE IF EXISTS Slots')
    cursor.execute('DROP TABLE IF EXISTS Vehicles')

    cursor.execute('''
    CREATE TABLE Slots (
        slot_id   TEXT PRIMARY KEY,
        size      INTEGER NOT NULL,
        status    TEXT NOT NULL DEFAULT 'free',
        position  INTEGER NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE Vehicles (
        vehicle_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT NOT NULL UNIQUE,
        size_needed  INTEGER NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE Bookings (
        booking_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id   INTEGER NOT NULL,
        slot_id      TEXT NOT NULL,
        start_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time     DATETIME NULL,
        part_start   INTEGER NULL,
        part_size    INTEGER NULL,
        algo_used    TEXT NULL,
        FOREIGN KEY (vehicle_id) REFERENCES Vehicles (vehicle_id),
        FOREIGN KEY (slot_id) REFERENCES Slots (slot_id)
    )
    ''')

    # Slot sizes use abstract capacity units: 1 = Bike, 2 = Car, 3 = SUV
    default_slots = [
        # Zone A
        ('A1', 1, 1), ('A2', 3, 2), ('A3', 1, 3), ('A4', 2, 4),  ('A5', 1, 5),
        ('A6', 2, 6), ('A7', 3, 7), ('A8', 1, 8), ('A9', 2, 9),  ('A10', 3, 10),
        # Zone B
        ('B1', 2, 11), ('B2', 1, 12), ('B3', 3, 13), ('B4', 2, 14), ('B5', 1, 15),
        ('B6', 3, 16), ('B7', 2, 17), ('B8', 1, 18), ('B9', 3, 19), ('B10', 2, 20),
        # Zone C
        ('C1', 3, 21), ('C2', 2, 22), ('C3', 1, 23), ('C4', 3, 24), ('C5', 2, 25),
        ('C6', 1, 26), ('C7', 3, 27), ('C8', 2, 28), ('C9', 1, 29), ('C10', 3, 30),
    ]

    cursor.executemany(
        "INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)",
        default_slots
    )

    connection.commit()
    connection.close()
    print(f"Initialized database with {len(default_slots)} slots.")


# Backwards compatibility alias
setup = initialize_database

if __name__ == '__main__':
    initialize_database()
