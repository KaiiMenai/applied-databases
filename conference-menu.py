# Conference Attendee Search Menu
# This script provides a simple command-line interface to search for conference attendees by name.
# It connects to a Neo4j database, retrieves matching attendees, and displays the results.
# Make sure to update the connection details (URI, USER, PASSWORD) to match your Neo4j setup before running the script.
# author: Kyra Menai Hamilton

import os
import sqlite3
from neo4j import GraphDatabase

class ConferenceDB:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, sqlite_db='appdbproj.db'):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.sqlite_db = sqlite_db
        self.sqlite_conn = sqlite3.connect(sqlite_db)
    
    def close(self):
        self.driver.close()
        self.sqlite_conn.close()
    
    # Option 1 - Neo4j search (FIXED - use AttendeeID string search)
    def search_speakers(self, search_string):
        query = """
        MATCH (speaker:Attendee)
        WHERE toString(speaker.AttendeeID) CONTAINS $name
        RETURN speaker.AttendeeID AS name
        ORDER BY speaker.AttendeeID
        """
        with self.driver.session(database="attendeenetwork") as session:
            result = session.run(query, name=search_string)
            return [record["name"] for record in result]

# Option 1 - SQLite search (FIXED - now searches speakerName with LIKE)
    def search_speakers_sessions(self, search_string):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT DISTINCT s.speakerName, s.sessionTitle, r.roomName
            FROM session s
            JOIN room r ON s.roomID = r.roomID
            WHERE LOWER(s.speakerName) LIKE LOWER(?)
            ORDER BY s.speakerName, s.sessionTitle
        """, (f'%{search_string}%',))
        results = cursor.fetchall()
        cursor.close()
        return results
    
    # Option 2 - Neo4j by company (FIXED - no Company property yet)
    def search_speakers_by_company(self, company_id):
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT a.attendeeName, a.attendeeID, c.companyName 
            FROM attendee a
            JOIN company c ON a.attendeeCompanyID = c.companyID
            WHERE c.companyID = ?
            ORDER BY a.attendeeName
        """, (company_id,))
        results = cursor.fetchall()
        cursor.close()
        return results

# Option 3 - Add new attendee (FIXED - now with specific ID input and validation)
    def add_new_attendee(self, attendee_id, name, dob, gender, company_id):
        """Add new attendee with SPECIFIC attendeeID to SQLite"""
        cursor = self.sqlite_conn.cursor()
        
        # Check if attendeeID already exists
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = ?", (attendee_id,))
        if cursor.fetchone():
            cursor.close()
            return False, f"*** ERROR *** Attendee ID: {attendee_id} already exists!"
        
        # Validate company_id exists
        cursor.execute("SELECT companyName FROM company WHERE companyID = ?", (company_id,))
        company = cursor.fetchone()
        if not company:
            cursor.close()
            return False, f"*** ERROR *** Company ID: {company_id} does not exist!"
        
        # Insert with SPECIFIC attendeeID
        cursor.execute("""
            INSERT INTO attendee (attendeeID, attendeeName, attendeeDOB, attendeeGender, attendeeCompanyID)
            VALUES (?, ?, ?, ?, ?)
        """, (attendee_id, name, dob, gender, company_id))
        
        self.sqlite_conn.commit()
        cursor.close()
        
        return True, f"Attendee successfully added! ID: {attendee_id}, {name}, {dob}, {gender} ({company[0]})"

# Option 4 - View connected attendees (FIXED - now checks Neo4j first, then SQLite, and shows connections)
    def view_connected_attendees(self, attendee_id):
        """Option 4: Find attendee + all CONNECTED_TO (both directions)"""
        
        # STEP 1: Check Neo4j first
        with self.driver.session(database="attendeenetwork") as session:
            query = """
            MATCH (target:Attendee {AttendeeID: $id})
            OPTIONAL MATCH (target)-[:CONNECTED_TO]-(connected:Attendee)
            RETURN target.AttendeeID AS targetID,
                collect(DISTINCT connected.AttendeeID) AS connectedIDs
            """
            result = session.run(query, id=attendee_id)
            neo4j_result = result.single()
        
        if not neo4j_result:
            # STEP 2: Check SQLite (exists but no Neo4j)
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = ?", (attendee_id,))
            sqlite_result = cursor.fetchone()
            cursor.close()
            
            if sqlite_result:
                return f"Attendee '{sqlite_result[0]}' (Attendee ID: {attendee_id}) \nAttendee Name: {sqlite_result[0]} \n----------------- \nNo connections"
            else:
                # STEP 3: Doesn't exist anywhere
                return f"*** ERROR *** Attendee ID {attendee_id} does not exist."
        
        # STEP 4: Neo4j attendee exists - FIXED SQLite IN clause
        target_id = neo4j_result["targetID"]
        connected_ids = neo4j_result["connectedIDs"] or []
        
        # Get names from SQLite - DYNAMIC IN clause fix
        cursor = self.sqlite_conn.cursor()
        all_ids = [target_id] + connected_ids
        placeholders = ','.join('?' * len(all_ids))
        cursor.execute(f"SELECT attendeeID, attendeeName FROM attendee WHERE attendeeID IN ({placeholders})", all_ids)
        names_dict = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.close()
        
        output = f"Attendee '{names_dict.get(target_id, 'Unknown')}' (ID: {target_id})\n\n"
        
        if connected_ids:
            output += "These attendees are connected:\n"
            output += "ID   | Name\n"
            output += "-----|--------------------\n"
            for conn_id in sorted(connected_ids):
                name = names_dict.get(conn_id, 'Unknown')
                output += f"{conn_id:4} | {name}\n"
        else:
            output += "\n----------------- \nNo connections"
        
        return output

# Option 5 - Add attendee connection (FIXED - now just a placeholder message)

# Menu display function
def print_menu():
    print("\n=== Conference Attendee Search ===")
    print("1 - View Speakers & Sessions")      # SQLite: speaker+session+room
    print("2 - View Attendees by Company")   # Neo4j
    print("3 - Add New Attendee")
    print("4 - View Connected Attendees")
    print("5 - Add Attendee Connection")
    print("6 - View Rooms")                  # SQLite
    print("x - Exit application")
    print("==================================")

def main():
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "attendeeNetwork"  
    
    db = ConferenceDB(URI, USER, PASSWORD)
    
    while True:
        print_menu()
        choice = input("Please enter your choice: ").strip()
        
        if choice == "1": # 1 - View Speakers & Sessions (FIXED - now uses SQLite to search speakerName with LIKE)
            print("\n View Speakers & Sessions \n-----------------")
            name_search = input("Enter speaker name letters: ").strip()
            speakers = db.search_speakers_sessions(name_search)  # ← SQLite!
            
            if speakers:
                print(f"\nFound {len(speakers)} sessions:")
                for speaker, title, room in speakers:
                    print(f"• {speaker} - '{title}' (Room: {room})")
            else:
                print("No speakers found with that name.")
                
        elif choice == "2": # 2 - View Attendees by Company (FIXED - now uses SQLite to search by company ID)
            print("\nView Attendees by Company \n-----------------")
            company_search = input("Enter Company ID: ").strip()
            attendees = db.search_attendees_by_company(company_search)
            
            if attendees:
                print(f"\nFound {len(attendees)} attendees:")
                for attendee in attendees:
                    print(f"- {attendee}")
            else:
                print("No attendees found from that company.")
                
        elif choice == "3": # 3 - Add New Attendee (FIXED - now with specific ID input and validation)
            print("\nAdd New Attendee \n-----------------")
    
            # 1. ATTENDEE ID VALIDATION LOOP
            while True:
                attendee_id = input("Attendee ID (e.g. 121): ").strip()
                if not attendee_id.isdigit():
                    print("*** ERROR *** Attendee ID must be a number!")
                    continue
        
                attendee_id = int(attendee_id)
        
                # Check if exists
                cursor = db.sqlite_conn.cursor()
                cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = ?", (attendee_id,))
                existing = cursor.fetchone()
                cursor.close()
        
                if existing:
                    print(f"*** ERROR *** Attendee ID {attendee_id} already exists! ({existing[0]})")
                    print("Please enter another ID.")
                    continue
                print(f"Attendee ID {attendee_id} is available!")
                break  # ID = DONE
    
            # 2. NAME VALIDATION LOOP
            while True:
                name = input("Attendee Name: ").strip()
                if not name:
                    print("*** ERROR *** Name cannot be empty!")
                    continue
                break  # Name = DONE
    
            # 3. DOB VALIDATION LOOP
            while True:
                dob = input("Date of Birth (YYYY-MM-DD): ").strip()
                # Basic date format check
                if len(dob) != 10 or dob[4] != '-' or dob[7] != '-':
                    print("*** ERROR *** Date format must be YYYY-MM-DD!")
                    continue
                break  # DOB = DONE
    
            # 4. GENDER VALIDATION LOOP
            while True:
                gender = input("Gender (Male/Female): ").strip().title()
                if gender not in ['Male', 'Female']:
                    print("*** ERROR *** Gender must be 'Male' or 'Female'")
                    continue
                break  # Gender = DONE
    
            # 5. COMPANY ID VALIDATION LOOP
            while True:
                company_id_input = input("Company ID (1-9): ").strip()
                if not company_id_input.isdigit() or not (1 <= int(company_id_input) <= 9):
                    print("*** ERROR *** Company ID must be 1-9!")
                    continue
        
                company_id = int(company_id_input)
        
                # Check company exists
                cursor = db.sqlite_conn.cursor()
                cursor.execute("SELECT companyName FROM company WHERE companyID = ?", (company_id,))
                company = cursor.fetchone()
                cursor.close()
        
                if not company:
                    print(f"*** ERROR *** Company ID {company_id} does not exist!")
                    continue
        
                print(f"Company {company_id}: {company[0]}")
                break  # Company = DONE
    
            # ALL VALIDATED - NOW INSERT MESSAGE OF CONFIRMATION
            success, message = db.add_new_attendee(attendee_id, name, dob, gender, company_id)
            print(message)
            
        elif choice == "4": # 4 - View Connected Attendees (FIXED - now checks Neo4j first, then SQLite, and shows connections)
            attendee_search = input("Enter Attendee ID: ").strip()
            
            # NON-NUMERIC CHECK FIRST
            if not attendee_search.isdigit():
                print("*** ERROR *** Invalid attendee ID")
                continue
            
            attendee_id = int(attendee_search)
            result = db.view_connected_attendees(attendee_id)
            print(f"\n{result}")
            
        elif choice == "5":
            print("\nAdd Attendee Connection \n-----------------")
            print("This feature is not implemented yet.")
        
        elif choice == "6":
            cursor = db.sqlite_conn.cursor()
            cursor.execute("SELECT roomName, capacity FROM room ORDER BY capacity DESC")
            rooms = cursor.fetchall()
            print("\nAll Rooms:")
            for room, capacity in rooms:
                print(f"- {room} (Capacity: {capacity})")
            cursor.close()
            
        elif choice == "x":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again")
    
    db.close()

if __name__ == "__main__":
    main()

# END