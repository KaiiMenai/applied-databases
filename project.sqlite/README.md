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


NOTE 
ammend dob restrictions -0 attendee can't be 9?

when connections made - have way to leave to mm

fix error when looking at attendees by company: 
- Enter Company ID: 3
Traceback (most recent call last):
  File "d:\Data_Analytics\Modules\applied-databases\conference-menu.py", line 468, in <module>
    main()
  File "d:\Data_Analytics\Modules\applied-databases\conference-menu.py", line 326, in main
    attendees = db.search_attendees_by_company(company_search)
  File "d:\Data_Analytics\Modules\applied-databases\conference-menu.py", line 119, in search_attendees_by_company
    session = session[:24] if len(session) > 24 else session.ljust(24)
TypeError: object of type 'NoneType' has no len()

# END