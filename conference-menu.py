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
    
    def search_speakers(self, search_string):
        query = """
        MATCH (speaker:Attendee)
        WHERE toString(speaker.AttendeeID) CONTAINS $name
        RETURN speaker.AttendeeID AS name
        """
        with self.driver.session(database="attendeenetwork") as session:
            result = session.run(query, name=search_string)
            return [record["name"] for record in result]

def print_menu():
    print("\n=== Conference Attendee Search ===")
    print("1 - View Speakers & Sessions")
    print("2 - View Attendees by Company")
    print("3 - Search attendees by name")
    print("4 - Search attendees by name")
    print("5 - Search attendees by name")
    print("6 - Search attendees by name")
    print("x - Exit application")
    print("==================================")

def main():
    # UPDATE THESE FROM NEO4J DESKTOP
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "attendeeNetwork"  # ← Change this!
    
    db = ConferenceDB(URI, USER, PASSWORD)  # ← Correct class name
    
    while True:
        print_menu()
        choice = input("Please enter your choice: ").strip()
        
        if choice == "1":
            name_search = input("Enter attendee ID letters: ").strip()
            speakers = db.search_speakers(name_search)
            
            if speakers:
                print(f"\nFound {len(speakers)} matching attendees:")
                for speaker in speakers:
                    print(f"- {speaker}")
            else:
                print("No attendees found with that name")
        
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again")
    
    db.close()

if __name__ == "__main__":
    main()