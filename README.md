# Applied Databases Project

author: Kyra Menai Hamilton

## Repository Contents

Reference files:

- appdbprojNeo4j.json - original neo4j relationship file here for reference.
- appdbproj.sql - original database file here for reference.
- project-plan.txt - outline of the plan for how the project will be conducted.
- create_an_db.py - python code to create a database in the repository in order to use the database through sqlite3 '''conn = sqlite3.connect('appdbproj.db')'''
- test.py - used to test if there were individuals called "Niamh" in the database.

Project files:

- requirements.txt - conditions required to conduct the project.
- attendeeNetwork.dump - the network connections for the conference database.
- appdbproj.db - the database formed from the original sql and used for reference in the project.
- conference-menu.py - python code that allows for exploration of the database and the relationships (12) and nodes (18).

## Set Up - START HERE

VM Setup (2 min):
1. Unzip -> double-click run.bat
2. Neo4j Desktop -> Import dump -> Start DB
3. python conference_menu.py -> Full demo.

# Basic Functionality

# Innovation

- Web UI using html - make it look pretty - it will be more user friendly imo - if use LLMs save prompt to make clear what I asked.
- API - Like in web services and applications - use flask (REST API)
- Matplotlib - room capacity visualisation

# END