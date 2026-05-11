# Applied Databases Project

This project is a menu-driven Python application for the Applied Databases module.

The specifics of this project are for a conference management database/system.

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
5. Run (in console):
   `python main.py`
6. Run (in console): `python api.py` then in web browser (go to): http://127.0.0.1:5000 - this has been buggy so step 7 was added.
7. Run (in new terminal): `python -m http.server 8000` then in web browser (go to): http://localhost:8000/web_ui.html

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

- Web UI using html - make it look pretty - it will be more user friendly imo - if use LLMs save prompt to make clear what I asked.
- API - Like in web services and applications - use flask (REST API)
- Matplotlib - room capacity visualisation

## Notes

Bugs during the running of the api and html. The following fix should be applied for now.

Terminal 1: `python api.py`  
Terminal 2: `python -m http.server 8000`  
Browser: `http://localhost:8000/web_ui.html`

# END