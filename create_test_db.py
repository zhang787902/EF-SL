import sqlite3
import os

# Create concert_singer database
os.makedirs('data/spider/database/concert_singer', exist_ok=True)
conn = sqlite3.connect('data/spider/database/concert_singer/concert_singer.sqlite')
c = conn.cursor()

c.execute('''CREATE TABLE singer (
    singer_id INTEGER PRIMARY KEY,
    name TEXT,
    country TEXT,
    song_name TEXT,
    song_release_year INTEGER,
    age INTEGER,
    is_male INTEGER
)''')

c.execute('''CREATE TABLE concert (
    concert_id INTEGER PRIMARY KEY,
    concert_name TEXT,
    theme TEXT,
    stadium_id INTEGER,
    year INTEGER
)''')

c.execute('''CREATE TABLE stadium (
    stadium_id INTEGER PRIMARY KEY,
    location TEXT,
    name TEXT,
    capacity INTEGER,
    highest INTEGER,
    lowest INTEGER,
    average INTEGER
)''')

c.execute('''CREATE TABLE singer_in_concert (
    concert_id INTEGER,
    singer_id INTEGER
)''')

# Insert sample data
c.execute("INSERT INTO singer VALUES (1, 'John Doe', 'USA', 'Hello', 2020, 30, 1)")
c.execute("INSERT INTO singer VALUES (2, 'Jane Smith', 'UK', 'World', 2019, 25, 0)")
c.execute("INSERT INTO concert VALUES (1, 'Rock Fest', 'Rock', 1, 2023)")
c.execute("INSERT INTO stadium VALUES (1, 'New York', 'Madison Square Garden', 20000, 25000, 15000, 18000)")

conn.commit()
conn.close()
print("Created concert_singer database")

# Create car_1 database
os.makedirs('data/spider/database/car_1', exist_ok=True)
conn = sqlite3.connect('data/spider/database/car_1/car_1.sqlite')
c = conn.cursor()

c.execute('''CREATE TABLE cars_data (
    id INTEGER PRIMARY KEY,
    mpg REAL,
    cylinders INTEGER,
    displacement REAL,
    horsepower TEXT,
    weight INTEGER,
    acceleration REAL,
    model_year INTEGER,
    origin TEXT,
    car_name TEXT
)''')

c.execute('''CREATE TABLE manufacturers (
    id INTEGER PRIMARY KEY,
    manufacturer_name TEXT,
    country TEXT
)''')

c.execute("INSERT INTO cars_data VALUES (1, 18.0, 8, 307.0, '130', 3504, 12.0, 70, 'USA', 'chevrolet chevelle malibu')")
c.execute("INSERT INTO manufacturers VALUES (1, 'Chevrolet', 'USA')")

conn.commit()
conn.close()
print("Created car_1 database")
print("Test databases created successfully!")
