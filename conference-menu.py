from neo4j import GraphDatabase
import sys

class ConferenceDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def search_speakers(self, search_string):
        with self.driver.session() as session:
            query = """
            MATCH (speaker:Attendee)
            WHERE toLower(speaker.AttendeeID) CONTAINS toLower($name)
            RETURN speaker.AttendeeID AS name
            """
            result = session.run(query, name=search_string)
            return [record["name"] for record in result]

def print_menu():
    print("\n=== Conference Attendee Search ===")
    print("1. Search attendees by name")
    print("2. Exit")
    print("==================================")

def main():
    # UPDATE THESE CONNECTION DETAILS FROM NEO4J DESKTOP
    URI = "neo4j://localhost:7687"
    USER = "neo4j"
    PASSWORD = "attendeeNetwork"
    
    db = ConferenceDB(URI, USER, PASSWORD)
    
    while True:
        print_menu()
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == "1":
            name_search = input("Enter Speaker name: ").strip()
            speakers = db.search_speakers(name_search)
            
            if speakers:
                print(f"\nFound {len(speakers)} matching attendees:")
                for speaker in speakers:
                    print(f"- {speaker}")
            else:
                print("No Speakers found with that name")
        
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again")
    
    db.close()

if __name__ == "__main__":
    main()