# database.py
# Handles all SQLite database operations for Powerlang.

import sqlite3
import os
import random
import csv
from datetime import date, timedelta

DB_FILE = "powerlang.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dictionaries'")
    if cursor.fetchone() is None:
        cursor.execute('CREATE TABLE dictionaries (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
    if cursor.fetchone() is None:
        cursor.execute('''
            CREATE TABLE words (
                id INTEGER PRIMARY KEY, native_word TEXT NOT NULL, learned_word TEXT NOT NULL,
                notes TEXT, dictionary_id INTEGER NOT NULL,
                FOREIGN KEY (dictionary_id) REFERENCES dictionaries (id)
            )
        ''')
    cursor.execute("PRAGMA table_info(words)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'easiness' not in columns: cursor.execute("ALTER TABLE words ADD COLUMN easiness REAL DEFAULT 2.5")
    if 'interval' not in columns: cursor.execute("ALTER TABLE words ADD COLUMN interval INTEGER DEFAULT 1")
    if 'next_review_date' not in columns:
        today = date.today().isoformat()
        cursor.execute(f"ALTER TABLE words ADD COLUMN next_review_date TEXT DEFAULT '{today}'")
    conn.commit()
    conn.close()

def delete_dictionary(dict_id):
    """Deletes a dictionary and all words contained within it."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Delete words first to maintain foreign key integrity
    cursor.execute("DELETE FROM words WHERE dictionary_id = ?", (dict_id,))
    # Then delete the dictionary itself
    cursor.execute("DELETE FROM dictionaries WHERE id = ?", (dict_id,))
    conn.commit()
    conn.close()

def get_due_cards():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute("SELECT id, native_word, learned_word, easiness, interval, next_review_date FROM words WHERE next_review_date <= ?", (today,))
    due_cards = cursor.fetchall()
    conn.close()
    random.shuffle(due_cards)
    return due_cards

def update_word_srs(word_id, easiness, interval, next_review_date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE words SET easiness = ?, interval = ?, next_review_date = ? WHERE id = ?", (easiness, interval, next_review_date.isoformat(), word_id))
    conn.commit()
    conn.close()

def get_dictionaries():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM dictionaries ORDER BY name")
    dictionaries = cursor.fetchall()
    conn.close()
    return dictionaries

def create_dictionary(name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO dictionaries (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_words(dictionary_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, native_word, learned_word, notes FROM words WHERE dictionary_id = ? ORDER BY native_word", (dictionary_id,))
    words = cursor.fetchall()
    conn.close()
    return words

def add_word(native, learned, notes, dict_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute("INSERT INTO words (native_word, learned_word, notes, dictionary_id, easiness, interval, next_review_date) VALUES (?, ?, ?, ?, 2.5, 1, ?)", (native, learned, notes, dict_id, today))
    conn.commit()
    conn.close()

def update_word(word_id, native, learned, notes):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE words SET native_word = ?, learned_word = ?, notes = ? WHERE id = ?", (native, learned, notes, word_id))
    conn.commit()
    conn.close()

def delete_word(word_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()

def get_random_word():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT native_word, learned_word FROM words")
    all_words = cursor.fetchall()
    conn.close()
    if not all_words: return None
    return random.choice(all_words)

def get_random_words(count=20): # Default to 20 for the new quiz length
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT native_word, learned_word FROM words")
    all_words = cursor.fetchall()
    conn.close()
    if not all_words: return []
    if len(all_words) < count: count = len(all_words)
    return random.sample(all_words, count)

def export_all_to_csv(filepath):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query = "SELECT w.native_word, w.learned_word, w.notes, d.name FROM words w JOIN dictionaries d ON w.dictionary_id = d.id ORDER BY d.name, w.native_word"
    cursor.execute(query)
    all_words = cursor.fetchall()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['native_word', 'learned_word', 'notes', 'dictionary_name'])
        writer.writerows(all_words)
    conn.close()
    return len(all_words)

def import_from_csv(filepath):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    imported_count = 0
    dictionary_cache = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            try:
                native_word, learned_word, notes, dict_name = row
                dict_id = dictionary_cache.get(dict_name)
                if not dict_id:
                    cursor.execute("SELECT id FROM dictionaries WHERE name = ?", (dict_name,))
                    result = cursor.fetchone()
                    if result: dict_id = result[0]
                    else:
                        cursor.execute("INSERT INTO dictionaries (name) VALUES (?)", (dict_name,))
                        dict_id = cursor.lastrowid
                    dictionary_cache[dict_name] = dict_id
                today = date.today().isoformat()
                cursor.execute("INSERT INTO words (native_word, learned_word, notes, dictionary_id, easiness, interval, next_review_date) VALUES (?, ?, ?, ?, 2.5, 1, ?)", (native_word, learned_word, notes, dict_id, today))
                imported_count += 1
            except (ValueError, IndexError):
                print(f"Skipping malformed row: {row}")
                continue
    conn.commit()
    conn.close()
    return imported_count