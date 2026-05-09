# Applied Databases Project

This project is a menu-driven Python application for the Applied Databases module.

## Requirements

- Python 3
- MySQL
- Neo4j

## Setup

1. Import `appdbproj.sql` into MySQL.
2. Import the Neo4j data file into the Neo4j database expected by the project.
3. Update the MySQL and Neo4j passwords in `main.py`.
4. Install dependencies:
   `python -m pip install -r requirements.txt`
5. Run:
   `python main.py`

## Innovation

- Web UI using html - make it look pretty - it will be more user friendly imo - if use LLMs save prompt to make clear what I asked.
- API - Like in web services and applications - use flask (REST API)
- Matplotlib - room capacity visualisation

## Notes

- The project uses MySQL for conference data.
- The project uses Neo4j for attendee connections.
- Rooms are cached after first viewing, as required by the specification.

# END