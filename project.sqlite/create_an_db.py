# The database.

# For ease for the assessment I decided that sqlite would be more user friendly than MySQL. 
# The parts for the project would all then be in one place.

# author: Kyra Menai Hamilton

# I used an LLM (Perplexity) and asked it to help me rephrase the database in a way that would be suitable and meet sql3lite requirements due to the syntax differences between it and MySQL.  

import sqlite3

# Connect to SQLite database (creates file if it doesn't exist)
conn = sqlite3.connect('appdbproj.db')
conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign keys

sql = """
-- Drop tables if they exist (in reverse order for foreign keys)
DROP TABLE IF EXISTS registration;
DROP TABLE IF EXISTS session;
DROP TABLE IF EXISTS attendee;
DROP TABLE IF EXISTS room;
DROP TABLE IF EXISTS company;

-- Create tables (SQLite syntax)
CREATE TABLE company (
    companyID INTEGER PRIMARY KEY,
    companyName TEXT NOT NULL,
    industry TEXT NOT NULL
);

CREATE TABLE attendee (
    attendeeID INTEGER PRIMARY KEY,
    attendeeName TEXT NOT NULL,
    attendeeDOB DATE NOT NULL,
    attendeeGender TEXT NOT NULL CHECK(attendeeGender IN ('Male', 'Female')),
    attendeeCompanyID INTEGER NOT NULL,
    FOREIGN KEY (attendeeCompanyID) REFERENCES company(companyID)
);

CREATE TABLE room (
    roomID INTEGER PRIMARY KEY,
    roomName TEXT NOT NULL,
    capacity INTEGER NOT NULL
);

CREATE TABLE session (
    sessionID INTEGER PRIMARY KEY,
    sessionTitle TEXT NOT NULL,
    speakerName TEXT NOT NULL,
    sessionDate DATE NOT NULL,
    roomID INTEGER NOT NULL,
    FOREIGN KEY (roomID) REFERENCES room(roomID)
);

CREATE TABLE registration (
    registrationID INTEGER PRIMARY KEY,
    attendeeID INTEGER NOT NULL,
    sessionID INTEGER NOT NULL,
    registeredAt DATETIME NOT NULL,
    FOREIGN KEY (attendeeID) REFERENCES attendee(attendeeID),
    FOREIGN KEY (sessionID) REFERENCES session(sessionID)
);
"""

conn.executescript(sql)

# Insert your data
companies = [
    (1, 'DataNova', 'Analytics'),
    (2, 'CloudSprint', 'Cloud'),
    (3, 'NeoRetail', 'Retail Tech'),
    (4, 'GreenGrid', 'Energy'),
    (5, 'MedAxis', 'Healthcare Tech'),
    (6, 'FinPilot', 'FinTech'),
    (7, 'EduSpark', 'EdTech'),
    (8, 'LogiCore', 'Logistics'),
    (9, 'WindyDays', 'Energy')
]

conn.executemany("INSERT INTO company VALUES (?, ?, ?)", companies)

attendees = [
    (101, 'Ava Murphy', '1994-02-11', 'Female', 1),
    (102, 'Liam Byrne', '1990-02-24', 'Male', 2),
    (103, 'Noah Doyle', '1988-07-03', 'Male', 3),
    (104, 'Emma Walsh', '1995-07-19', 'Female', 4),
    (105, 'Sophia Ryan', '1992-11-05', 'Female', 5),
    (106, 'Jack Kelly', '1987-11-14', 'Male', 6),
    (107, "Mia O'Brien", '1996-03-09', 'Female', 7),
    (108, 'Charlie Nolan', '1993-03-28', 'Male', 8),
    (109, 'Ella Finn', '1991-09-17', 'Female', 1),
    (110, 'Cian Roche', '1989-09-08', 'Male', 2),
    (111, 'Grace Power', '1997-01-12', 'Female', 3),
    (112, 'Daniel Quinn', '1990-01-29', 'Male', 4),
    (113, 'Ruby Keane', '1998-05-21', 'Female', 5),
    (114, 'Adam Hayes', '1986-05-30', 'Male', 6),
    (115, 'Chloe Hunt', '1994-08-02', 'Female', 7),
    (116, 'Ben Casey', '1992-08-25', 'Male', 8),
    (117, 'Lucy Reid', '1993-12-06', 'Female', 1),
    (118, 'Evan Brady', '1988-12-18', 'Male', 2),
    (119, 'Holly Farrell', '1995-06-10', 'Female', 3),
    (120, 'Sean Dempsey', '1987-06-27', 'Male', 4)
]

conn.executemany("INSERT INTO attendee VALUES (?, ?, ?, ?, ?)", attendees)

rooms = [
    (1, 'Main Hall', 300),
    (2, 'Graph Lab', 120),
    (3, 'Cloud Suite', 180),
    (4, 'Innovation Room', 90),
    (5, 'Workshop Studio', 60),
    (6, 'Executive Lounge', 40)
]

conn.executemany("INSERT INTO room VALUES (?, ?, ?)", rooms)

sessions = [
    (201, 'Modern Data Pipelines', 'Dr. Niamh Burke', '2025-05-12', 1),
    (202, 'Scaling Neo4j for Recommendations', 'Prof. Alan Shaw', '2025-05-12', 2),
    (203, 'Secure API Design', 'Ruth Collins', '2025-05-12', 3),
    (204, 'AI in Healthcare Operations', 'Dr. Sara Khan', '2025-05-13', 1),
    (205, 'Building Reliable ETL Jobs', 'Conor Daly', '2025-05-13', 4),
    (206, 'FinTech Risk Signals', 'Marta Silva', '2025-05-13', 6),
    (207, 'Graph Modelling Workshop', 'Prof. Alan Shaw', '2025-05-14', 2),
    (208, 'Cloud Cost Optimisation', 'Ruth Collins', '2025-05-14', 3),
    (209, 'Customer 360 with SQL', 'Dr. Niamh Burke', '2025-05-14', 1),
    (210, 'EdTech Product Analytics', 'Grace Lennon', '2025-05-15', 4),
    (211, 'Logistics Forecasting', 'Patrick Moore', '2025-05-15', 5),
    (212, 'Energy Dashboards at Scale', 'Aisling Kerr', '2025-05-15', 3)
]

conn.executemany("INSERT INTO session VALUES (?, ?, ?, ?, ?)", sessions)

# Add some registrations (first 10 for demo)
registrations = [
    (301, 101, 201, '2025-04-01 09:00:00'),
    (302, 102, 202, '2025-04-01 09:15:00'),
    (303, 103, 203, '2025-04-01 09:25:00'),
    (304, 104, 204, '2025-04-01 09:30:00'),
    (305, 105, 204, '2025-04-01 09:35:00')
]

conn.executemany("INSERT INTO registration VALUES (?, ?, ?, ?)", registrations)

conn.commit()
conn.close()

print("appdbproj.db created successfully!")
print("Tables: company, attendee, room, session, registration")
print("Data loaded: 9 companies, 20 attendees, 6 rooms, 12 sessions")

# END