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
        
    def close(self):
        if self.mysql_conn:
            self.mysql_conn.close()
        self.neo4j_driver.close()
        
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

