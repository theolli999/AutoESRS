import sqlite3

def create_database(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sourceDescriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        description TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def fetch_data(db_name, query):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def addData(db_name, source, description):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sourceDescriptions (source, description) VALUES (?, ?)", (source, description))
    conn.commit()
    conn.close()

def getDescription(db_name, source):
    print(source)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM sourceDescriptions WHERE source=?", (source,))
    result = cursor.fetchone()
    conn.close()
    return result


def main():
    db_name = 'data.db'
    create_database(db_name)
    print("Database created and table setup completed.")

if __name__ == "__main__":
    main()