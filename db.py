import sqlite3
import threading

db_lock = threading.Lock()

def create_database(db_name):
    conn = sqlite3.connect(db_name, timeout=30)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS descriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        description TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def fetch_data(db_name, query):
    with db_lock:
        conn = sqlite3.connect(db_name, timeout=30)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results

def clear_data(db_name):
    with db_lock:
        conn = sqlite3.connect(db_name, timeout=30)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM descriptions")
        conn.commit()
        conn.close()

def addData(db_name, source, description):
    print("About to add data to database")
    with db_lock:
        print("Adding data to database")
        conn = sqlite3.connect(db_name, timeout=30)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO descriptions (source, description) VALUES (?, ?)", (source, description))
        conn.commit()
        conn.close()
        print("Commited")

def getDescription(db_name, source):
    with db_lock:
        conn = sqlite3.connect(db_name, timeout=30)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM descriptions WHERE source=?", (source,))
        result = cursor.fetchone()
        conn.close()
        return result

def main():
    db_name = 'descriptions.db'
    create_database(db_name)
    print("Database created and table setup completed.")

if __name__ == "__main__":
    main()