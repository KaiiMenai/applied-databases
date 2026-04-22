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
        
        if choice == "1":
            name_search = input("Enter speaker name letters: ").strip()
            speakers = db.search_speakers_sessions(name_search)  # ← SQLite!
            
            if speakers:
                print(f"\nFound {len(speakers)} sessions:")
                for speaker, title, room in speakers:
                    print(f"• {speaker} - '{title}' (Room: {room})")
            else:
                print("No speakers found with that name.")
                
        elif choice == "2":
            company_search = input("Enter Company ID: ").strip()
            speakers = db.search_speakers_by_company(company_search)
            
            if speakers:
                print(f"\nFound {len(speakers)} attendees:")
                for speaker in speakers:
                    print(f"- {speaker}")
            else:
                print("No attendees found from that company.")
        
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