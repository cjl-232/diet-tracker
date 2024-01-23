from contextlib import closing
import sqlite3

_DB_FILE = 'db.sqlite3'

def _execute_query(
    query: str,
    params = (),
    escalate_exceptions: bool = False
):
    try:
        with closing(sqlite3.connect(_DB_FILE)) as connection:
            connection.execute("PRAGMA foreign_keys = 1")
            query = connection.execute(query, params).fetchall()
            connection.commit()
            return query
    except sqlite3.Error as error:
        print('Error executing query: {}.'.format(error))
        if escalate_exceptions:
            raise error


def _create_weight_table():
    _execute_query('''
        CREATE TABLE IF NOT EXISTS weight_observations (
            id INTEGER PRIMARY KEY,
            weight REAL NOT NULL CHECK (weight >= 0.0),
            timestamp DEFAULT CURRENT_TIMESTAMP
        )
    ''')    

def _create_consumption_tables():
    _execute_query('''
        CREATE TABLE IF NOT EXISTS consumables (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            unit_calories REAL NOT NULL CHECK (unit_calories >= 0.0),
            unit_label TEXT NOT NULL DEFAULT "unit"
        )
    ''')
    _execute_query('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY,
            timestamp DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    _execute_query('''
        CREATE TABLE IF NOT EXISTS meal_components(
            id INTEGER PRIMARY KEY,
            consumable_id INTEGER NOT NULL REFERENCES consumables
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            meal_id INTEGER NOT NULL REFERENCES meals
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            quantity REAL NOT NULL CHECK (quantity > 0.0)
        )
    ''')
    
    
def create_tables():
    _create_weight_table()
    _create_consumption_tables()
        
def append_weight_observation(value: float):
    _execute_query(
        'INSERT INTO weight_observations (weight) VALUES (?)',
        (value,),
    )
    
def append_consumable(
    name: str, 
    calories: float, 
    unit_label: str = 'unit'
):
    _execute_query(
        '''
            INSERT INTO consumables (
                name, unit_calories, unit_label
            )
            VALUES (
                :name, :calories, :unit_label
            )
        ''',
        {'name': name, 'calories': calories, 'unit_label': unit_label}
    )
    
def append_meal(components : list[tuple[int, float]]):
    _execute_query('INSERT INTO meals DEFAULT VALUES')
    meal_id = _execute_query('SELECT MAX(id) FROM meals')[0][0]
    try:
        for component in components:
            _execute_query(
                '''
                    INSERT INTO meal_components (
                        consumable_id, meal_id, quantity
                    ) VALUES (
                        :consumable_id, :meal_id, :quantity
                    )
                ''',
                params = {
                    'consumable_id': component[0],
                    'meal_id': meal_id,
                    'quantity': component[1],
                },
                escalate_exceptions = True,
            )
    except BaseException as error:
        print('Failed to append meal.')
        _execute_query('DELETE FROM meals WHERE id = ?', (meal_id,))