-- appdbproj MySQL database
DROP DATABASE IF EXISTS appdbproj;
CREATE DATABASE appdbproj;
USE appdbproj;

CREATE TABLE company (
    companyID INT PRIMARY KEY,
    companyName VARCHAR(100) NOT NULL,
    industry VARCHAR(60) NOT NULL
);

CREATE TABLE attendee (
    attendeeID INT PRIMARY KEY,
    attendeeName VARCHAR(100) NOT NULL,
    attendeeDOB DATE NOT NULL,
    attendeeGender ENUM('Male','Female') NOT NULL,
    attendeeCompanyID INT NOT NULL,
    FOREIGN KEY (attendeeCompanyID) REFERENCES company(companyID)
);

CREATE TABLE room (
    roomID INT PRIMARY KEY,
    roomName VARCHAR(80) NOT NULL,
    capacity INT NOT NULL
);

CREATE TABLE session (
    sessionID INT PRIMARY KEY,
    sessionTitle VARCHAR(150) NOT NULL,
    speakerName VARCHAR(100) NOT NULL,
    sessionDate DATE NOT NULL,
    roomID INT NOT NULL,
    FOREIGN KEY (roomID) REFERENCES room(roomID)
);

CREATE TABLE registration (
    registrationID INT PRIMARY KEY,
    attendeeID INT NOT NULL,
    sessionID INT NOT NULL,
    registeredAt DATETIME NOT NULL,
    FOREIGN KEY (attendeeID) REFERENCES attendee(attendeeID),
    FOREIGN KEY (sessionID) REFERENCES session(sessionID)
);

INSERT INTO company VALUES
(1,'DataNova','Analytics'),
(2,'CloudSprint','Cloud'),
(3,'NeoRetail','Retail Tech'),
(4,'GreenGrid','Energy'),
(5,'MedAxis','Healthcare Tech'),
(6,'FinPilot','FinTech'),
(7,'EduSpark','EdTech'),
(8,'LogiCore','Logistics'),
(9,'WindyDays','Energy');

INSERT INTO attendee VALUES
(101,'Ava Murphy','1994-02-11','Female',1),
(102,'Liam Byrne','1990-02-24','Male',2),
(103,'Noah Doyle','1988-07-03','Male',3),
(104,'Emma Walsh','1995-07-19','Female',4),
(105,'Sophia Ryan','1992-11-05','Female',5),
(106,'Jack Kelly','1987-11-14','Male',6),
(107,'Mia O''Brien','1996-03-09','Female',7),
(108,'Charlie Nolan','1993-03-28','Male',8),
(109,'Ella Finn','1991-09-17','Female',1),
(110,'Cian Roche','1989-09-08','Male',2),
(111,'Grace Power','1997-01-12','Female',3),
(112,'Daniel Quinn','1990-01-29','Male',4),
(113,'Ruby Keane','1998-05-21','Female',5),
(114,'Adam Hayes','1986-05-30','Male',6),
(115,'Chloe Hunt','1994-08-02','Female',7),
(116,'Ben Casey','1992-08-25','Male',8),
(117,'Lucy Reid','1993-12-06','Female',1),
(118,'Evan Brady','1988-12-18','Male',2),
(119,'Holly Farrell','1995-06-10','Female',3),
(120,'Sean Dempsey','1987-06-27','Male',4);

INSERT INTO room VALUES
(1,'Main Hall',300),
(2,'Graph Lab',120),
(3,'Cloud Suite',180),
(4,'Innovation Room',90),
(5,'Workshop Studio',60),
(6,'Executive Lounge',40);

INSERT INTO session VALUES
(201,'Modern Data Pipelines','Dr. Niamh Burke','2025-05-12',1),
(202,'Scaling Neo4j for Recommendations','Prof. Alan Shaw','2025-05-12',2),
(203,'Secure API Design','Ruth Collins','2025-05-12',3),
(204,'AI in Healthcare Operations','Dr. Sara Khan','2025-05-13',1),
(205,'Building Reliable ETL Jobs','Conor Daly','2025-05-13',4),
(206,'FinTech Risk Signals','Marta Silva','2025-05-13',6),
(207,'Graph Modelling Workshop','Prof. Alan Shaw','2025-05-14',2),
(208,'Cloud Cost Optimisation','Ruth Collins','2025-05-14',3),
(209,'Customer 360 with SQL','Dr. Niamh Burke','2025-05-14',1),
(210,'EdTech Product Analytics','Grace Lennon','2025-05-15',4),
(211,'Logistics Forecasting','Patrick Moore','2025-05-15',5),
(212,'Energy Dashboards at Scale','Aisling Kerr','2025-05-15',3);

INSERT INTO registration VALUES
(301,101,201,'2025-04-01 09:00:00'),
(302,102,202,'2025-04-01 09:15:00'),
(303,103,203,'2025-04-01 09:25:00'),
(304,104,204,'2025-04-01 09:30:00'),
(305,105,204,'2025-04-01 09:35:00'),
(306,106,206,'2025-04-01 09:40:00'),
(307,107,210,'2025-04-01 09:45:00'),
(308,108,211,'2025-04-01 09:50:00'),
(309,109,209,'2025-04-01 10:00:00'),
(310,110,208,'2025-04-01 10:05:00'),
(311,111,202,'2025-04-01 10:10:00'),
(312,112,205,'2025-04-01 10:15:00'),
(313,113,204,'2025-04-01 10:20:00'),
(314,114,206,'2025-04-01 10:25:00'),
(315,115,210,'2025-04-01 10:30:00'),
(316,116,211,'2025-04-01 10:35:00'),
(317,117,201,'2025-04-01 10:40:00'),
(318,118,208,'2025-04-01 10:45:00'),
(319,119,209,'2025-04-01 10:50:00'),
(320,120,212,'2025-04-01 10:55:00'),
(321,101,202,'2025-04-02 09:00:00'),
(322,102,209,'2025-04-02 09:10:00'),
(323,103,207,'2025-04-02 09:20:00'),
(324,104,212,'2025-04-02 09:30:00'),
(325,105,203,'2025-04-02 09:40:00'),
(326,106,205,'2025-04-02 09:50:00'),
(327,107,201,'2025-04-02 10:00:00'),
(328,108,208,'2025-04-02 10:10:00'),
(329,109,204,'2025-04-02 10:20:00'),
(330,110,206,'2025-04-02 10:30:00');