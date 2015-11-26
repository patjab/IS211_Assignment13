import sqlite3


def main():
    """Loads schema.sql into hw13.db"""
    conn = sqlite3.connect('hw13.db')
    f = open('schema.sql','r')
    sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
