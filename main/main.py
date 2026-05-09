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

# This is to ensure that the MySQL and Neo4j are closed correctly when the app is closed.
    def close(self):
        if self.mysql_conn:
            self.mysql_conn.close()
        self.neo4j_driver.close()

# Option 1 - View Speakers & Sessions
    def search_speakers(self, search_string):
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
            return None, "No speakers found of that name"

        return results, None

# Option 2 - View Attendees by Company
    def search_attendees_by_company(self, company_id):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        company = cursor.fetchone()
        if not company:
            cursor.close()
            return None, None, f"Company with ID {company_id} doesn't exist"

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
            return company[0], None, f"No attendees found for {company[0]}"

        return company[0], rows, None

# Option 3 - Add New Attendee
    def add_new_attendee(self, attendee_id, name, dob, gender, company_id):
        cursor = self.mysql_conn.cursor()

        # 1. Check duplicate attendee ID first (spec Figure 13)
        #    Pass as-is; if the value is non-numeric MySQL returns no rows here,
        #    and the INSERT will later raise error 1366 (spec Figure 16).
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee_id,))
        if cursor.fetchone():
            cursor.close()
            return False, f"*** ERROR *** Attendee ID: {attendee_id} already exists"

        # 2. Validate gender (spec Figure 14)
        if gender not in ("Male", "Female"):
            cursor.close()
            return False, "*** ERROR *** Gender must be Male/Female"

        # 3. Check company exists (spec Figure 15)
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        if not cursor.fetchone():
            cursor.close()
            return False, f"*** ERROR *** Company ID: {company_id} does not exist"

        # 4. Attempt INSERT — any remaining invalid values (invalid ID, invalid DOB, etc.)
        #    are caught here and surfaced as the raw DB error (spec Figures 16 & 17)
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

# Option 4 - View Connected Attendees
    def view_connected_attendees(self, attendee_id):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (attendee_id,))
        mysql_attendee = cursor.fetchone()
        cursor.close()

        if not mysql_attendee:
            return None, None, "*** ERROR *** Attendee does not exist"

        with self.neo4j_driver.session(database="appdbprojNeo4j") as session:
            result = session.run("""
                MATCH (a:Attendee {AttendeeID: $id})
                OPTIONAL MATCH (a)-[:CONNECTED_TO]-(b:Attendee)
                RETURN a.AttendeeID AS attendeeID, collect(DISTINCT b.AttendeeID) AS connections
            """, id=attendee_id)
            record = result.single()

        if not record:
            return mysql_attendee[0], None, None

        connections = [x for x in record["connections"] if x is not None]

        if not connections:
            return mysql_attendee[0], None, None

        cursor = self.mysql_conn.cursor()
        placeholders = ",".join(["%s"] * len(connections))
        cursor.execute(f"SELECT attendeeID, attendeeName FROM attendee WHERE attendeeID IN ({placeholders})", connections)
        rows = cursor.fetchall()
        cursor.close()

        sorted_rows = sorted(rows, key=lambda r: r[0])
        return mysql_attendee[0], sorted_rows, None

# Option 5 - Add Attendee Connection
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

# Option 6 - View Rooms
    def view_rooms(self):
        if self.room_cache is None:
            cursor = self.mysql_conn.cursor()
            # Order by capacity DESC so the largest rooms appear first.
            # Result is cached — any rooms added to MySQL after the first call will not appear until the application is restarted.
            cursor.execute("SELECT roomID, roomName, capacity FROM room ORDER BY capacity DESC")
            self.room_cache = cursor.fetchall()
            cursor.close()

        if not self.room_cache:
            return None, "No rooms found"

        return self.room_cache, None

# ── MENU ──
def print_menu():
    print("Conference Management")
    print("---------------------")
    print()
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

# ── Table Specification──
def print_table(headers, rows):
    """Print a neatly aligned table with the given headers and rows."""
    # FIX: corrected enumerate spelling; headers and rows are now proper parameters
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, value in enumerate(row):       # was: enumurate
            widths[i] = max(widths[i], len(str(value)))

    print(" | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)))

# ── Main loop ──
def main():
    db = ConferenceDB(
        mysql_host="localhost",
        mysql_user="root",
        mysql_password="YOUR_MYSQL_PASSWORD",  # PLEASE CHANGE THIS TO YOUR MYSQL PASSWORD - root
        mysql_database="appdbproj",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="YOUR_NEO4J_PASSWORD"   # PLEASE CHANGE THIS TO YOUR NEO4J PASSWORD
    )
    try:
        while True:
            print()
            print_menu()
            choice = input().strip().lower()

            # ── Option 1: View Speakers & Sessions ──
            if choice == "1":
                speaker = input("Enter speaker name : ").strip()
                # Header and separator always print, matching spec Figures 4 & 5
                print(f"Session Details For :  {speaker}")
                print("-" * 54)
                rows, err = db.search_speakers(speaker)
                if err:
                    # No match — show message then return to menu
                    print(err)
                else:
                    # Show speaker name, session title, room in aligned table form
                    print_table(["Speaker Name", "Session Title", "Room"], rows)

            # ── Option 2: View Attendees by Company ──
            elif choice == "2":
                while True:
                    company = input("Enter Company ID : ").strip()

                    # Keep re-prompting until a positive integer is entered (spec Figure 8)
                    if not (company.lstrip('-').isdigit() and int(company) > 0):
                        continue

                    company_id = int(company)
                    company_name, rows, err = db.search_attendees_by_company(company_id)

                    if err:
                        if company_name:
                            # Company exists but has no attendees — print header first, then the "No attendees found" message (spec Figure 10)
                            print(f"{company_name}  Attendees")
                        # else: company doesn't exist — just print the error (spec Figure 9)
                        print(err)
                        # Re-prompt in both error cases (spec section 3.1.4.1)
                        continue

                    # Success — show company name header then attendee table
                    print(f"{company_name}  Attendees")
                    print_table(["Name", "DOB", "Session Title", "Speaker", "Room"], rows)
                    break

            # ── Option 3: Add New Attendee ──
            elif choice == "3":
                print("Add New Attendee")
                print("----------------")
                # Collect all fields as raw strings so that invalid values, (e.g. "asdf" for ID or DOB) reach the DB and produce the correct error messages shown in spec Figures 16 & 17
                attendee_id = input("Attendee ID : ").strip()
                name        = input("Name : ").strip()
                dob         = input("DOB : ").strip()
                gender      = input("Gender : ").strip().title()
                company_id  = input("Company ID : ").strip()

                ok, msg = db.add_new_attendee(attendee_id, name, dob, gender, company_id)
                print(msg)
                # Both success and error messages are printed then the user is returned to the main menu — no re-prompt loop for option 3

            # ── Option 4: View Connected Attendees ──
            elif choice == "4":
                while True:
                    raw = input("Enter Attendee ID : ").strip()

                    # Non-numeric input: re-prompt (spec Figure 21, section 3.1.6.1)
                    if not raw.lstrip('-').isdigit():
                        print("*** ERROR *** Invalid attendee ID")
                        continue

                    attendee_id = int(raw)
                    name, rows, err = db.view_connected_attendees(attendee_id)

                    if err:
                        # Attendee not in MySQL or Neo4j (spec Figure 20). Just show the error and return to menu — no re-prompt
                        print(err)
                        break

                    # Attendee found — name and separator always print first
                    print(f"Attendee Name:   {name}")
                    print("-" * 20)

                    if rows:
                        # Has CONNECTED_TO relationships — show ID and name of each connected attendee in a table (spec Figure 18)
                        print("These attendees are connected:")
                        print_table(["Attendee ID", "Name"], rows)
                    else:
                        # Exists in MySQL but not Neo4j, or Neo4j node has no connections in either direction (spec Figure 19)
                        print("No connections")

                    break

            # ── Option 5: Add Attendee Connection ──
            elif choice == "5":
                while True:
                    raw1 = input("Enter Attendee 1 ID : ").strip()
                    raw2 = input("Enter Attendee 2 ID : ").strip()

                    # Both IDs must be positive integers (spec Figure 29) - isdigit() rejects negatives, floats, and any non-numeric string
                    if not (raw1.isdigit() and raw2.isdigit()):
                        print("*** ERROR *** Attendee IDs must be numbers")
                        continue   # re-prompt both IDs

                    attendee1_id = int(raw1)
                    attendee2_id = int(raw2)
                    ok, msg = db.add_attendee_connection(attendee1_id, attendee2_id)
                    print(msg)

                    if not ok:
                        # All error conditions loop back to ID entry (spec Figures 26-29):
                        # - cannot connect to him/herself
                        # - already connected
                        # - one or both IDs do not exist in MySQL
                        continue   # re-prompt both IDs

                    break   # success — return to main menu

            # ── Option 6: View Rooms ──
            elif choice == "6":
                # FIX: view_rooms now returns (rows, err); rows is a list, not a string
                rows, err = db.view_rooms()
                if err:
                    print(err)
                else:
                    print_table(["RoomID", "RoomName", "Capacity"], rows)

            # ── Exit ──
            elif choice == "x":
                break

            # ── Anything else: redisplay menu ──
            # (the while True loop handles this automatically)

    finally:
        db.close()

if __name__ == "__main__":
    main()

# END