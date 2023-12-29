import sqlite3

connection = sqlite3.connect('instance/database.db')

# print("initializing db...")
# with open('schema.sql') as f:
#     connection.executescript(f.read())
# print("initialized!")

print("seeding db...")
with open("seed.sql") as f:
    connection.executescript(f.read())
print("seeded!")

connection.commit()
connection.close()
print("finished!")
