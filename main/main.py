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
            database=mysql_database,
            # FIX: MySQL 8+ defaults to caching_sha2_password which older versions of
            # mysql-connector-python (bundled with Anaconda) do not support.
            # Forcing mysql_native_password resolves the NotSupportedError on startup.
            auth_plugin="mysql_native_password"
        )
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.room_cache = None

    # This is to ensure that the MySQL and Neo4j connections are closed correctly
    # when the app exits.
    def close(self):
        if self.mysql_conn:
            self.mysql_conn.close()
        self.neo4j_driver.close()


# ── Option 1 - View Speakers & Sessions ───────────────────────────────────────
    def search_speakers(self, search_string):
        # FIX: removed the early-exit guard for empty strings. The method now always
        # queries the database so that an empty search correctly returns "No speakers
        # found" rather than short-circuiting before hitting MySQL.
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

        # FIX: original method returned a plain formatted string. It now returns a
        # (rows, error) tuple so that main() can unpack it consistently and pass
        # the rows directly to print_table().
        return results, None


# ── Option 2 - View Attendees by Company ──────────────────────────────────────
    def search_attendees_by_company(self, company_id):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        company = cursor.fetchone()
        if not company:
            cursor.close()
            # FIX: original method returned 2 values. Now returns 3 — (company_name,
            # rows, error) — so main() can always unpack the same number of values
            # regardless of which error condition is hit.
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
            # FIX: company_name is included even in the no-attendees error so that
            # main() can print the company header before the error message,
            # matching spec Figure 10.
            return company[0], None, f"No attendees found for {company[0]}"

        return company[0], rows, None


# ── Option 3 - Add New Attendee ───────────────────────────────────────────────
    def add_new_attendee(self, attendee_id, name, dob, gender, company_id):
        cursor = self.mysql_conn.cursor()

        # FIX: validation order was wrong in the original — gender was checked before
        # the duplicate ID check. Reordered to match the spec's own figures:
        # Figure 13 (duplicate ID) → Figure 14 (bad gender) → Figure 15 (bad company)
        # → Figures 16/17 (DB catches remaining bad values like non-numeric ID or DOB).

        # Step 1 — duplicate ID check (spec Figure 13)
        # Inputs are kept as raw strings throughout so that non-numeric values like
        # "asdf" fall through to the INSERT and trigger the correct DB error (Figure 16).
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee_id,))
        if cursor.fetchone():
            cursor.close()
            return False, f"*** ERROR *** Attendee ID: {attendee_id} already exists"

        # Step 2 — gender validation (spec Figure 14)
        # FIX: gender check was missing entirely from the original code.
        if gender not in ("Male", "Female"):
            cursor.close()
            return False, "*** ERROR *** Gender must be Male/Female"

        # Step 3 — company existence check (spec Figure 15)
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        if not cursor.fetchone():
            cursor.close()
            return False, f"*** ERROR *** Company ID: {company_id} does not exist"

        # Step 4 — attempt INSERT; any remaining bad values (e.g. non-numeric ID,
        # invalid DOB) are caught here and returned as the raw DB error message
        # so the exact text from Figures 16 & 17 is preserved.
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


# ── Option 4 - View Connected Attendees ───────────────────────────────────────
    def view_connected_attendees(self, attendee_id):
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (attendee_id,))
        mysql_attendee = cursor.fetchone()
        cursor.close()

        if not mysql_attendee:
            # FIX: original returned a plain string. Now returns a (name, rows, error)
            # tuple so main() can unpack 3 values consistently in all code paths.
            return None, None, "*** ERROR *** Attendee does not exist"

        with self.neo4j_driver.session(database="appdbprojNeo4j") as session:
            result = session.run("""
                MATCH (a:Attendee {AttendeeID: $id})
                OPTIONAL MATCH (a)-[:CONNECTED_TO]-(b:Attendee)
                RETURN a.AttendeeID AS attendeeID, collect(DISTINCT b.AttendeeID) AS connections
            """, id=attendee_id)
            record = result.single()

        # Attendee exists in MySQL but has no node in Neo4j — return name with no rows
        if not record:
            return mysql_attendee[0], None, None

        connections = [x for x in record["connections"] if x is not None]

        # Attendee node exists in Neo4j but has no CONNECTED_TO relationships
        if not connections:
            return mysql_attendee[0], None, None

        # Look up the names of all connected attendees from MySQL and sort by ID
        cursor = self.mysql_conn.cursor()
        placeholders = ",".join(["%s"] * len(connections))
        cursor.execute(
            f"SELECT attendeeID, attendeeName FROM attendee WHERE attendeeID IN ({placeholders})",
            connections
        )
        rows = cursor.fetchall()
        cursor.close()

        sorted_rows = sorted(rows, key=lambda r: r[0])
        return mysql_attendee[0], sorted_rows, None


# ── Option 5 - Add Attendee Connection ────────────────────────────────────────
    def add_attendee_connection(self, attendee1_id, attendee2_id):
        # Self-connection guard (spec Figure 26)
        if attendee1_id == attendee2_id:
            return False, "*** ERROR *** An attendee cannot connect to him/herself"

        # Both IDs must exist in MySQL before touching Neo4j (spec Figure 28)
        cursor = self.mysql_conn.cursor()
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee1_id,))
        a1 = cursor.fetchone()
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee2_id,))
        a2 = cursor.fetchone()
        cursor.close()

        if not a1 or not a2:
            return False, "*** ERROR *** One or both attendee IDs do not exist"

        with self.neo4j_driver.session(database="appdbprojNeo4j") as session:
            # Check for existing connection in either direction (spec Figure 27)
            existing = session.run("""
                MATCH (a:Attendee {AttendeeID: $id1})-[r:CONNECTED_TO]-(b:Attendee {AttendeeID: $id2})
                RETURN count(r) AS c
            """, id1=attendee1_id, id2=attendee2_id).single()["c"]

            if existing > 0:
                return False, "*** ERROR *** These attendees are already connected"

            # MERGE creates the nodes if they don't already exist in Neo4j,
            # so this handles the case where one attendee has no node yet (spec Figure 24).
            session.run("""
                MERGE (a:Attendee {AttendeeID: $id1})
                MERGE (b:Attendee {AttendeeID: $id2})
                MERGE (a)-[:CONNECTED_TO]->(b)
            """, id1=attendee1_id, id2=attendee2_id)

        return True, f"Attendee {attendee1_id} is now connected to Attendee {attendee2_id}"


# ── Option 6 - View Rooms ──────────────────────────────────────────────────────
    def view_rooms(self):
        if self.room_cache is None:
            cursor = self.mysql_conn.cursor()
            # FIX: original query ordered by roomID. Changed to ORDER BY capacity DESC
            # so the largest rooms appear at the top, matching the spec requirement.
            # FIX: result is stored in self.room_cache on the first call. Any rooms
            # added to MySQL after this point won't appear until the app is restarted,
            # satisfying the caching requirement in spec section 3.1.8.
            cursor.execute("SELECT roomID, roomName, capacity FROM room ORDER BY capacity DESC")
            self.room_cache = cursor.fetchall()
            cursor.close()

        if not self.room_cache:
            return None, "No rooms found"

        # FIX: original returned a pre-formatted string. Now returns a (rows, error)
        # tuple so main() can pass the raw rows directly to print_table().
        return self.room_cache, None


# ── Helpers ────────────────────────────────────────────────────────────────────

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


def print_table(headers, rows):
    # FIX: original function had two bugs:
    #   1. "enumurate" typo caused a NameError at runtime.
    #   2. headers and rows were referenced as globals that were never defined;
    #      they are now proper parameters passed in by the caller.
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))

    print(" | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)))


# ── Main loop ──────────────────────────────────────────────────────────────────

def main():
    db = ConferenceDB(
        mysql_host="localhost",
        mysql_user="root",
        mysql_password="yourpassword",  # PLEASE CHANGE THIS TO YOUR MYSQL PASSWORD
        mysql_database="appdbproj",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="root"   # PLEASE CHANGE THIS TO YOUR NEO4J PASSWORD
    )
    try:
        while True:
            print()
            print_menu()
            choice = input().strip().lower()

            # ── Option 1: View Speakers & Sessions ────────────────────────────
            if choice == "1":
                speaker = input("Enter speaker name : ").strip()

                # Header and separator always print before the result or error
                # message, matching spec Figures 4 (results) and 5 (no results).
                print(f"Session Details For :  {speaker}")
                print("-" * 54)

                # FIX: original code unpacked the return value as (rows, err) but
                # search_speakers returned a single string. Now correctly unpacks
                # the (rows, error) tuple returned by the fixed method.
                rows, err = db.search_speakers(speaker)
                if err:
                    print(err)
                else:
                    print_table(["Speaker Name", "Session Title", "Room"], rows)

            # ── Option 2: View Attendees by Company ───────────────────────────
            elif choice == "2":
                while True:
                    company = input("Enter Company ID : ").strip()

                    # FIX: original code accepted the first valid-format ID and broke
                    # out even on error. Now loops until a positive integer is entered,
                    # silently re-prompting on non-numeric or zero/negative input (Figure 8).
                    if not (company.lstrip('-').isdigit() and int(company) > 0):
                        continue

                    company_id = int(company)

                    # FIX: original code unpacked 2 values; method now returns 3.
                    company_name, rows, err = db.search_attendees_by_company(company_id)

                    if err:
                        if company_name:
                            # Company found but has no attendees — spec Figure 10
                            # requires the company name header to print before the error.
                            print(f"{company_name}  Attendees")
                        # Company doesn't exist — spec Figure 9, no header needed.
                        print(err)
                        # FIX: both error conditions re-prompt (spec section 3.1.4.1).
                        continue

                    print(f"{company_name}  Attendees")
                    print_table(["Name", "DOB", "Session Title", "Speaker", "Room"], rows)
                    break

            # ── Option 3: Add New Attendee ────────────────────────────────────
            elif choice == "3":
                # Header shown as per spec Figure 11
                print("Add New Attendee")
                print("----------------")

                # FIX: inputs are collected as raw strings (not cast to int here)
                # so that invalid values like "asdf" for ID or DOB reach the database
                # and produce the exact error text shown in spec Figures 16 & 17.
                attendee_id = input("Attendee ID : ").strip()
                name        = input("Name : ").strip()
                dob         = input("DOB : ").strip()
                gender      = input("Gender : ").strip().title()
                company_id  = input("Company ID : ").strip()

                ok, msg = db.add_new_attendee(attendee_id, name, dob, gender, company_id)
                print(msg)
                # FIX: no re-prompt loop for option 3 — spec does not require one.
                # After any outcome (success or error) the user returns to the main menu.

            # ── Option 4: View Connected Attendees ────────────────────────────
            elif choice == "4":
                while True:
                    raw = input("Enter Attendee ID : ").strip()

                    # FIX: original code caught ValueError after the fact; now checks
                    # upfront. Non-numeric input re-prompts with the correct error
                    # message (spec Figure 21, section 3.1.6.1).
                    if not raw.lstrip('-').isdigit():
                        print("*** ERROR *** Invalid attendee ID")
                        continue

                    attendee_id = int(raw)

                    # FIX: original unpacked 3 values from a method that returned a
                    # plain string. Now correctly unpacks the (name, rows, error) tuple.
                    name, rows, err = db.view_connected_attendees(attendee_id)

                    if err:
                        # Attendee not in MySQL or Neo4j (spec Figure 20).
                        # FIX: original used continue here, causing an unwanted re-prompt.
                        # Changed to break — spec only requires re-prompt for non-numeric
                        # input, not for a valid-but-nonexistent ID.
                        print(err)
                        break

                    # Attendee found — name and separator always print (Figures 18 & 19)
                    print(f"Attendee Name:   {name}")
                    print("-" * 20)

                    if rows:
                        # Has connections — show table (spec Figure 18)
                        print("These attendees are connected:")
                        print_table(["Attendee ID", "Name"], rows)
                    else:
                        # In MySQL but not Neo4j, or no connections (spec Figure 19)
                        print("No connections")

                    break

            # ── Option 5: Add Attendee Connection ─────────────────────────────
            elif choice == "5":
                while True:
                    raw1 = input("Enter Attendee 1 ID : ").strip()
                    raw2 = input("Enter Attendee 2 ID : ").strip()

                    # FIX: original used lstrip('-').isdigit() which accidentally let
                    # negative numbers through as "numeric". str.isdigit() is stricter —
                    # it rejects negatives, floats, and all non-numeric strings (Figure 29).
                    if not (raw1.isdigit() and raw2.isdigit()):
                        print("*** ERROR *** Attendee IDs must be numbers")
                        continue

                    attendee1_id = int(raw1)
                    attendee2_id = int(raw2)
                    ok, msg = db.add_attendee_connection(attendee1_id, attendee2_id)
                    print(msg)

                    if not ok:
                        # FIX: all four error conditions (self-connect, already connected,
                        # non-existent ID, non-numeric) re-prompt from Attendee 1 ID,
                        # matching spec section 3.1.7.1 and Figures 26-29.
                        continue

                    break

            # ── Option 6: View Rooms ───────────────────────────────────────────
            elif choice == "6":
                # FIX: original passed the return value of view_rooms() directly to
                # print_table(), but the method returned a formatted string, not a list.
                # Now correctly unpacks the (rows, error) tuple and passes rows to
                # print_table() only on success.
                rows, err = db.view_rooms()
                if err:
                    print(err)
                else:
                    print_table(["RoomID", "RoomName", "Capacity"], rows)

            # ── Exit ───────────────────────────────────────────────────────────
            elif choice == "x":
                break

            # ── Anything else: spec section 3.1.10 — redisplay menu ───────────
            # The while True loop handles this automatically by falling through
            # to the next iteration without printing anything extra.

    finally:
        db.close()


if __name__ == "__main__":
    main()

# END