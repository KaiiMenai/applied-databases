# Conference Attendee Search Menu
# This script provides a simple command-line interface to search for conference attendees by name.
# It connects to a Neo4j database, retrieves matching attendees, and displays the results.
# Make sure to update the connection details (URI, USER, PASSWORD) to match your Neo4j setup before running the script.
# author: Kyra Menai Hamilton

from neo4j import GraphDatabase

class ConferenceDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
# Query to search for speakers by name (case-insensitive, partial match)
    def search_speakers(self, search_string):
        query = """
        MATCH (speaker:Attendee)
        WHERE toString(speaker.AttendeeID) CONTAINS $name
        RETURN speaker.AttendeeID AS name
        """
        with self.driver.session(database="attendeenetwork") as session:
            result = session.run(query, name=search_string)
            return [record["name"] for record in result]

# Query to search for speakers by Company (valid (numeric) company ID) - maybe this needs to be an integer instead of a string?
    def search_speakers_by_company(self, search_string):
        query = """
        MATCH (speaker:Attendee)
        WHERE toString(speaker.Company) = $company
        RETURN speaker.AttendeeID AS name
        """
        with self.driver.session(database="attendeenetwork") as session:
            result = session.run(query, company=search_string)
            return [record["name"] for record in result]

def print_menu():
    print("\n=== Conference Attendee Search ===")
    print("1 - View Speakers & Sessions")
    print("2 - View Attendees by Company")
    print("3 - Add New Attendee")
    print("4 - View Connected Attendees")
    print("5 - Add Attendee Connection")
    print("6 - View Rooms")
    print("x - Exit application")
    print("==================================")

def main():
    # UPDATE THESE FROM NEO4J DESKTOP
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "attendeeNetwork"  
    
    db = ConferenceDB(URI, USER, PASSWORD)  
    
    while True:
        print_menu()
        choice = input("Please enter your choice: ").strip()
        
        if choice == "1":
            name_search = input("Enter speaker name: ").strip()
            speakers = db.search_speakers(name_search)
            
            if speakers:
                print(f"\nFound {len(speakers)} matching attendees:")
                for speaker in speakers:
                    print(f"- {speaker}")
            else:
                print("No attendees found with that name.")
        
        elif choice == "2":
            company_search = input("Enter Company name: ").strip()
            speakers = db.search_speakers_by_company(company_search)
            
            if speakers:
                print(f"\nFound {len(speakers)} matching attendees from that company:")
                for speaker in speakers:
                    print(f"- {speaker}")
            elif not company_search:
                print("Please enter a valid company ID.")
            else:
                print("No attendees found from that company.")
        
        elif choice == "x":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again")
    
    db.close()

if __name__ == "__main__":
    main()