import sqlite3

def setup():
    db = sqlite3.connect('parking_system.db')
    cur = db.cursor()

    cur.execute('DROP TABLE IF EXISTS Bookings')
    cur.execute('DROP TABLE IF EXISTS Slots')
    cur.execute('DROP TABLE IF EXISTS Vehicles')

    cur.execute('''
    CREATE TABLE Slots (
        slot_id   VARCHAR(10) PRIMARY KEY,
        size      INT NOT NULL,
        status    VARCHAR(20) NOT NULL DEFAULT 'free',
        position  INT NOT NULL
    )
    ''')

    cur.execute('''
    CREATE TABLE Vehicles (
        vehicle_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number VARCHAR(20) NOT NULL UNIQUE,
        size_needed  INT NOT NULL
    )
    ''')

    cur.execute('''
    CREATE TABLE Bookings (
        booking_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id    INT NOT NULL,
        slot_id       VARCHAR(10) NOT NULL,
        strategy_used VARCHAR(20) NOT NULL,
        start_time    DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time      DATETIME NULL
    )
    ''')

    zone_a = [
        ('A1', 1, 1), ('A2', 3, 2), ('A3', 1, 3), ('A4', 2, 4),  ('A5', 1, 5),
        ('A6', 2, 6), ('A7', 3, 7), ('A8', 1, 8), ('A9', 2, 9),  ('A10', 3, 10),
    ]
    zone_b = [
        ('B1', 2, 11), ('B2', 1, 12), ('B3', 3, 13), ('B4', 2, 14), ('B5', 1, 15),
        ('B6', 3, 16), ('B7', 2, 17), ('B8', 1, 18), ('B9', 3, 19), ('B10', 2, 20),
    ]
    zone_c = [
        ('C1', 3, 21), ('C2', 2, 22), ('C3', 1, 23), ('C4', 3, 24), ('C5', 2, 25),
        ('C6', 1, 26), ('C7', 3, 27), ('C8', 2, 28), ('C9', 1, 29), ('C10', 3, 30),
    ]

    for s in zone_a + zone_b + zone_c:
        cur.execute("INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)", s)

    db.commit()
    db.close()
    print("Database ready with 30 parking slots.")


if __name__ == '__main__':
    setup()
