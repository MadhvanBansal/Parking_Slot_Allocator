CREATE DATABASE IF NOT EXISTS parking_system;

USE parking_system;


DROP TABLE IF EXISTS Fragmentation_Log;
DROP TABLE IF EXISTS Bookings;
DROP TABLE IF EXISTS Slots;
DROP TABLE IF EXISTS Vehicles;


CREATE TABLE Slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    size INT NOT NULL,
    status ENUM('free', 'occupied') NOT NULL DEFAULT 'free',
    position INT NOT NULL
);


CREATE TABLE Vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL UNIQUE,
    size_needed INT NOT NULL
);


CREATE TABLE Bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    slot_id INT NOT NULL,
    strategy_used ENUM('Best-Fit') NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME NULL
);


CREATE TABLE Fragmentation_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    free_gap_count INT NOT NULL,
    total_wasted_space INT NOT NULL
);


DESC Slots;

DESC Vehicles;

DESC Bookings;

DESC Fragmentation_Log;
 
ALTER TABLE Slots
    ADD COLUMN zone ENUM('small', 'medium', 'large') NOT NULL AFTER size,
    ADD COLUMN slot_label VARCHAR(5) NOT NULL UNIQUE AFTER zone;

ALTER TABLE Vehicles
    MODIFY COLUMN size_needed ENUM('small', 'medium', 'large') NOT NULL;

ALTER TABLE Bookings
    MODIFY COLUMN strategy_used ENUM('first-fit', 'best-fit', 'worst-fit') NOT NULL;

DELETE FROM Fragmentation_Log;
DELETE FROM Bookings;
DELETE FROM Slots;

ALTER TABLE Slots AUTO_INCREMENT = 1;

INSERT INTO Slots (size, zone, slot_label, status, position) VALUES
(10, 'small', 'A1', 'free', 1),
(10, 'small', 'A2', 'free', 2),
(10, 'small', 'A3', 'free', 3),
(10, 'small', 'A4', 'free', 4),
(10, 'small', 'A5', 'free', 5),
(10, 'small', 'A6', 'free', 6),
(10, 'small', 'A7', 'free', 7),
(10, 'small', 'A8', 'free', 8),
(10, 'small', 'A9', 'free', 9),
(10, 'small', 'A10', 'free', 10),
(20, 'medium', 'B1', 'free', 1),
(20, 'medium', 'B2', 'free', 2),
(20, 'medium', 'B3', 'free', 3),
(20, 'medium', 'B4', 'free', 4),
(20, 'medium', 'B5', 'free', 5),
(20, 'medium', 'B6', 'free', 6),
(20, 'medium', 'B7', 'free', 7),
(20, 'medium', 'B8', 'free', 8),
(20, 'medium', 'B9', 'free', 9),
(20, 'medium', 'B10', 'free', 10),
(30, 'large', 'C1', 'free', 1),
(30, 'large', 'C2', 'free', 2),
(30, 'large', 'C3', 'free', 3),
(30, 'large', 'C4', 'free', 4),
(30, 'large', 'C5', 'free', 5),
(30, 'large', 'C6', 'free', 6),
(30, 'large', 'C7', 'free', 7),
(30, 'large', 'C8', 'free', 8),
(30, 'large', 'C9', 'free', 9),
(30, 'large', 'C10', 'free', 10);

CREATE INDEX idx_slots_zone_status
ON Slots(zone, status);

SELECT slot_id, slot_label
FROM Slots
WHERE status = 'free'
  AND zone = 'small'
ORDER BY position ASC
LIMIT 1;

START TRANSACTION;

SELECT slot_id, slot_label
FROM Slots
WHERE status = 'free'
  AND zone = 'small'
ORDER BY position ASC
LIMIT 1;

UPDATE Slots
SET status = 'occupied'
WHERE slot_id = 1;

INSERT INTO Bookings (vehicle_id, slot_id, strategy_used)
VALUES (1, 1, 'best-fit');

COMMIT;
