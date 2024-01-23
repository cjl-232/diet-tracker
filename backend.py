from contextlib import closing
from datetime import datetime
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
    _execute_query("""
        CREATE TABLE IF NOT EXISTS weight_observations (
            id INTEGER PRIMARY KEY,
            weight REAL NOT NULL CHECK (weight >= 0.0),
            timestamp INTEGER NOT NULL DEFAULT (unixepoch('now'))
        )
    """)    

def _create_consumption_tables():
    _execute_query("""
        CREATE TABLE IF NOT EXISTS consumable_groups (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    _execute_query("""
        CREATE TABLE IF NOT EXISTS consumables (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            consumable_group_id INTEGER REFERENCES consumable_groups
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            unit_calories REAL NOT NULL CHECK (unit_calories >= 0.0),
            unit_label TEXT NOT NULL DEFAULT "unit"
        )
    """)
    _execute_query("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY,
            timestamp INTEGER NOT NULL DEFAULT (unixepoch('now'))
        )
    """)
    _execute_query("""
        CREATE INDEX IF NOT EXISTS timestamp_index 
            ON meals(timestamp)
    """)
    _execute_query("""
        CREATE TABLE IF NOT EXISTS meal_components(
            id INTEGER PRIMARY KEY,
            consumable_id INTEGER NOT NULL
                REFERENCES consumables
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            meal_id INTEGER NOT NULL
                REFERENCES meals
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            quantity REAL NOT NULL CHECK (quantity > 0.0)
        )
    """)
    
    
def create_tables():
    _create_weight_table()
    _create_consumption_tables()
        
def append_weight_observation(value: float):
    _execute_query(
        'INSERT INTO weight_observations (weight) VALUES (?)',
        (value,),
    )
    
def append_consumable_group(name: str):
    _execute_query(
        'INSERT INTO consumable_groups (name) VALUES (?)',
        (name,),
    )
    
def append_consumable(
    name: str,
    calories: float,
    unit_label: str = 'unit',
    consumable_group_id: int | None = None,
):
    _execute_query(
        """
            INSERT INTO consumables (
                name, unit_calories, unit_label, consumable_group_id
            )
            VALUES (
                :name, :calories, :unit_label, :consumable_group_id
            )
        """,
        {
            'name': name, 
            'calories': calories, 
            'unit_label': unit_label,
            'consumable_group_id': consumable_group_id,
        }
    )
    
def append_meal(components : list[tuple[int, float]]):
    _execute_query('INSERT INTO meals DEFAULT VALUES')
    meal_id = _execute_query('SELECT MAX(id) FROM meals')[0][0]
    try:
        for component in components:
            _execute_query(
                """
                    INSERT INTO meal_components (
                        consumable_id, meal_id, quantity
                    ) VALUES (
                        :consumable_id, :meal_id, :quantity
                    )
                """,
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
        
        
#SUM THE RHS, FILTER THE LHS, LEFT JOIN RHS TO THE LHS
def get_weight_history(
    start_datetime : datetime = None,
    end_datetime : datetime = None,
):
    query = 'SELECT weight, timestamp FROM weight_observations'
    conditions = []
    timestamp_bounds = []
    if start_datetime is not None:
        conditions.append('timestamp >= ?')
        timestamp_bounds.append(int(start_datetime.timestamp()))
    if end_datetime is not None:
        conditions.append('timestamp <= ?')
        timestamp_bounds.append(int(end_datetime.timestamp()))
    if len(conditions) != 0:
        query += ' WHERE ' + ' AND '.join(conditions)
        
    return _execute_query(query, timestamp_bounds)

def get_meal_calories(
    start_datetime : datetime = None,
    end_datetime : datetime = None,
):
    query = """
        SELECT m.timestamp, COALESCE(SUM(mc.quantity * c.unit_calories), 0)
        FROM meals m
        LEFT JOIN meal_components mc ON m.id = mc.meal_id
        LEFT JOIN consumables c ON c.id = mc.consumable_id
    """
    conditions = []
    timestamp_bounds = []
    if start_datetime is not None:
        conditions.append('m.timestamp >= ?')
        timestamp_bounds.append(int(start_datetime.timestamp()))
    if end_datetime is not None:
        conditions.append('m.timestamp <= ?')
        timestamp_bounds.append(int(end_datetime.timestamp()))
    if len(conditions) != 0:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' GROUP BY m.id'

    return _execute_query(query, timestamp_bounds)
    