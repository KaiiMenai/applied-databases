# Applied Databases Project

This project is a menu-driven Python application for the Applied Databases module.

The specifics of this project are for a conference management database/system.

author: Kyra Menai Hamilton

## Overview

Documents for this project:

- main.py
- appdbproj.sql
- appdbproj.db (for reference)
- appdbprojNeo4j.json
- appdbprojNeo4j.dump (for reference)

Innovation files:

- innovation.docx
- api.py
- web_ui.html

## Requirements

- Python 3
- MySQL
- Neo4j

## Setup

1. Import `appdbproj.sql` into MySQL. (`mysql -u root -p appdbproj < appdbproj.sql`).
2. Import the Neo4j data file into the Neo4j database. (`appdbprojNeo4j.json` or dump (Neo4j Desktop)).
3. Update the MySQL and Neo4j passwords (lines ~450, ~40, respectively) in `main.py` and `api.py`.
4. Install dependencies:
   `python -m pip install -r requirements.txt`
5. Update passwords for MySQL and Neo4j in `main.py` (lines 280 & 284) and `api.py` (lines 33 & 37).
6. Run (in console):
   `python main.py`
7. Run (in console): `python api.py` then in web browser (go to): http://127.0.0.1:5000 - *this has been buggy so step 8 was added*.
8. Run (in new terminal): `python -m http.server 8000` then in web browser (go to): http://localhost:8000/web_ui.html

## Endpoints

| GET | POST | Description |
|-----|------|-------------|
| `/api/speakers?name=dr` | | Option 1 |
| `/api/attendees/2` | | Option 2 |
| | `/api/attendee` | Option 3 |
| `/api/connections/101` | | Option 4 |
| | `/api/connections` | Option 5 |
| `/api/rooms` | | Option 6 |
| `/api/rooms/chart` | | Visualisation |

## Innovation

- Web UI Dashboard (HTML/CSS/JavaScript)
- Flask REST API (7 endpoints)
- Matplotlib Room Capacity Visualisation

## Notes

mysql has some connectivity issues. If bug occurs:

1. Open Services and stop the MySQL service.
2. Open Notepad and create a file like `C:\mysql-init.txt` containing exactly:
`ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';`
3. Open Command Prompt as Administrator.
4. Change to your MySQL bin folder, for example:
in powershell
`cd "C:\Program Files\MySQL\MySQL Server 8.0\bin"`
5. Start MySQL with the init file:
in powershell
`mysqld --init-file=C:\\mysql-init.txt`
6. After it starts successfully, delete `C:\mysql-init.txt`.
7. Start the MySQL service normally again.  
(Ref - asked LLM why I was getting a specific error)

Bugs during the running of the  api and html. The following fix should be applied for now.

Terminal 1: `python api.py`  
Terminal 2: `python -m http.server 8000`  
Browser: `http://localhost:8000/web_ui.html`

# END