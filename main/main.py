# main.py
# This is the main entry point for the app. It initialises the app and starts the main loop.
# author: Kyra Menai Hamilton

import mysql.connector
from neo4j import GraphDatabase

class ConferenceDB:
    def __init__(self, mysql_host, mysql_user, mysql_password, mysql_database, neo4j_uri, neo4j_user, neo4j_password):
        self.mysql_conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.room_cache = None
        
# This is to ensure that the My SQL and Neo4j are closed correctly when the app is closed.
    def close(self):
        if self.mysql_conn:
            self.mysql_conn.close()
        self.neo4j_driver.close()

# Option 1 - View Speakers and Sessions
    def search_speakers(self, search_string):
        if not search_string:
            return "No speakers found of that name."
        cursor = self.mysql_conn.cursor()
        cursor.execute("""
            SELECT DISTINCT s.speakerName, s.sessionTitle, r.roomName
            FROM session s
            LEFT JOIN room r ON s.roomID = r.roomID
            WHERE LOWER(s.speakerName) LIKE LOWER(%s)
            ORDER BY s.speakerName, s.sessionTitle
        """, (f"%{search_string}%",))
        results = cursor.fetchall()
        cursor.close()
        if not results:
            return "No speakers found of that name"
        output = f"Session Details For : {search_string}\n" + "-" * 54 + "\n"
        
        for speaker, session_title, room_name in results:
            output += f"{speaker} | {session_title} | {room_name}"

        return output.rstrip()

# Optuion 2 - View Attendees by Company
    def search_attendees_by_company(self, company_id):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        company = cursor.fetchone()
        if not company:
            cursor.close()
            return None, f"Company with ID {company_id} doesn't exist"
        cursor.execute("""
            SELECT a.attendeeName, a.attendeeDOB, s.sessionTitle, s.speakerName, r.roomName
            FROM attendee a
            LEFT JOIN registration reg ON a.attendeeID = reg.attendeeID
            LEFT JOIN session s ON reg.sessionID = s.sessionID
            LEFT JOIN room r ON s.roomID = r.roomID
            WHERE a.attendeeCompanyID = %s
            ORDER BY a.attendeeName, s.sessionTitle
        """, (company_id,))
        rows = cursor.fetchall()
        cursor.close()
        if not rows:
            return company[0], f"No attendees found for {company[0]}"
        return company[0], rows

# Option 3 - Add New Attendee
    def add_new_attendee(self, attendee_id, name, dob, gender, company_id):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee_id,))
        if cursor.fetchone():
            cursor.close()
            return False, f"*** ERROR *** Attendee ID: {attendee_id} already exists"
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        company = cursor.fetchone()
        if not company:
            cursor.close()
            return False, f"*** ERROR *** Company ID: {company_id} does not exist"
        try:
            cursor.execute("""
                INSERT INTO attendee (attendeeID, attendeeName, attendeeDOB, attendeeGender, attendeeCompanyID)
                VALUES (%s, %s, %s, %s, %s)
            """, (attendee_id, name, dob, gender, company_id))
            self.mysql_conn.commit()
        except mysql.connector.Error as e:
            self.mysql_conn.rollback()
            cursor.close()
            return False, f"*** ERROR *** {e}"
        cursor.close()
        return True, "Attendee successfully added"

    def view_connected_attendees(self, attendee_id):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (attendee_id,))
        mysql_attendee = cursor.fetchone()
        cursor.close()
        if not mysql_attendee:
            return "*** ERROR *** Attendee does not exist"
        with self.neo4j_driver.session(database="appdbprojNeo4j") as session:
            result = session.run("""
                MATCH (a:Attendee {AttendeeID: $id})
                OPTIONAL MATCH (a)-[:CONNECTED_TO]-(b:Attendee)
                RETURN a.AttendeeID AS attendeeID, collect(DISTINCT b.AttendeeID) AS connections
            """, id=attendee_id)
            record = result.single()
            
        if not record:
            return f"Attendee Name: {mysql_attendee[0]} No connections"
        connections = [x for x in record["connections"] if x is not None]
        
        if not connections:
            return f"Attendee Name: {mysql_attendee[0]} No connections"
        
        cursor = self.mysql_conn.cursor()
        placeholders = ",".join(["%s"] * len(connections))
        cursor.execute(f"SELECT attendeeID, attendeeName FROM attendee WHERE attendeeID IN ({placeholders})", connections)
        names = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.close()
        output = f"Attendee Name: {mysql_attendee[0]} These attendees are connected:"
        
        for cid in sorted(connections):
            output += f"{cid} | {names.get(cid, 'Unknown')}"
        return output.rstrip()

    def add_attendee_connection(self, attendee1_id, attendee2_id):
        if attendee1_id == attendee2_id:
            return False, "*** ERROR *** An attendee cannot connect to him/herself"
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee1_id,))
        a1 = cursor.fetchone()
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee2_id,))
        a2 = cursor.fetchone()
        cursor.close()
        if not a1 or not a2:
            return False, "*** ERROR *** One or both attendee IDs do not exist"
        with self.neo4j_driver.session(database="appdbprojNeo4j") as session:
            existing = session.run("""
                MATCH (a:Attendee {AttendeeID: $id1})-[r:CONNECTED_TO]-(b:Attendee {AttendeeID: $id2})
                RETURN count(r) AS c
            """, id1=attendee1_id, id2=attendee2_id).single()["c"]
            if existing > 0:
                return False, "*** ERROR *** These attendees are already connected"
            session.run("""
                MERGE (a:Attendee {AttendeeID: $id1})
                MERGE (b:Attendee {AttendeeID: $id2})
                MERGE (a)-[:CONNECTED_TO]->(b)
            """, id1=attendee1_id, id2=attendee2_id)
        return True, f"Attendee {attendee1_id} is now connected to Attendee {attendee2_id}"

    def view_rooms(self):
        if self.room_cache is None:
            cursor = self.mysql_conn.cursor()
            cursor.execute("SELECT roomID, roomName, capacity FROM room ORDER BY roomID")
            self.room_cache = cursor.fetchall()
            cursor.close()
        if not self.room_cache:
            return "No rooms found"
        output = "RoomID | RoomName | Capacity\n" + "-" * 30 + "\n"
        for room_id, room_name, capacity in self.room_cache:
            output += f"{room_id} | {room_name} | {capacity}\n"
        return output.rstrip()

def print_menu():
    print("Conference Management")
    print("---------------------")
    print("MENU")
    print("====")
    print("1 - View Speakers & Sessions")
    print("2 - View Attendees by Company")
    print("3 - Add New Attendee")
    print("4 - View Connected Attendees")
    print("5 - Add Attendee Connection")
    print("6 - View Rooms")
    print("x - Exit application")
    print("---------------------")
    print("Choice:", end=" ")

def main():
    db = ConferenceDB(
        mysql_host="localhost",
        mysql_user="root",
        mysql_password="YOUR_MYSQL_PASSWORD", # PLEASE CHANGE THIS TO YOUR MYSQL PASSWORD - root
        mysql_database="appdbproj",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="YOUR_NEO4J_PASSWORD" # PLEASE CHANGE THIS TO YOUR NEO4J PASSWORD
    )
    try:
        while True:
            print()
            print_menu()
            choice = input().strip().lower()
            
            if choice == "1": # View Speakers and Sessions
                speaker = input("Enter speaker name : ").strip()
                print(db.search_speakers(speaker))
                
            elif choice == "2": # View Attendees by Company
                while True:
                    company = input("Enter Company ID : ").strip()
                    if company.isdigit() and int(company) > 0:
                        company_id = int(company)
                        break
                result = db.search_attendees_by_company(company_id)
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], str):
                    print(result[1])
                else:
                    company_name, rows = result
                    print(company_name)
                    for row in rows:
                        print(" | ".join(str(x) for x in row))
                        
            elif choice == "3":
                attendee_id = int(input("Attendee ID : ").strip())
                name = input("Name : ").strip()
                dob = input("DOB : ").strip()
                gender = input("Gender : ").strip().title()
                company_id = int(input("Company ID : ").strip())
                ok, msg = db.add_new_attendee(attendee_id, name, dob, gender, company_id)
                print(msg)
                
            elif choice == "4":
                attendee_id = int(input("Enter Attendee ID : ").strip())
                print(db.view_connected_attendees(attendee_id))
                
            elif choice == "5":
                attendee1_id = int(input("Enter Attendee 1 ID : ").strip())
                attendee2_id = int(input("Enter Attendee 2 ID : ").strip())
                ok, msg = db.add_attendee_connection(attendee1_id, attendee2_id)
                print(msg)
                
            elif choice == "6":
                print(db.view_rooms())
                
            elif choice == "x":
                break
    finally:
        db.close()

if __name__ == "__main__":
    main()

# END