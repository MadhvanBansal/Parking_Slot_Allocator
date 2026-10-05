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
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
