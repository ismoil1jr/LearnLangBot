import sqlite3
import os

DB_PATH = 'learnlangbot.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Create subcategories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
            UNIQUE(category_id, name)
        )
    ''')

    # Create topics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subcategory_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories (id) ON DELETE CASCADE,
            UNIQUE(subcategory_id, name)
        )
    ''')

    # Create lessons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            teacher_name TEXT NOT NULL,
            video_url TEXT NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# CRUD for categories
def create_category(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return category_id

def get_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM categories ORDER BY name')
    categories = cursor.fetchall()
    conn.close()
    return categories

def update_category(category_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE categories SET name = ? WHERE id = ?', (name, category_id))
    conn.commit()
    conn.close()

def delete_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()

# CRUD for subcategories
def create_subcategory(category_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO subcategories (category_id, name) VALUES (?, ?)', (category_id, name))
    subcategory_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return subcategory_id

def get_subcategories_by_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM subcategories WHERE category_id = ? ORDER BY name', (category_id,))
    subcategories = cursor.fetchall()
    conn.close()
    return subcategories

def update_subcategory(subcategory_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE subcategories SET name = ? WHERE id = ?', (name, subcategory_id))
    conn.commit()
    conn.close()

def delete_subcategory(subcategory_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM subcategories WHERE id = ?', (subcategory_id,))
    conn.commit()
    conn.close()

# CRUD for topics
def create_topic(subcategory_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO topics (subcategory_id, name) VALUES (?, ?)', (subcategory_id, name))
    topic_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return topic_id

def get_topics_by_subcategory(subcategory_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM topics WHERE subcategory_id = ? ORDER BY name', (subcategory_id,))
    topics = cursor.fetchall()
    conn.close()
    return topics

def update_topic(topic_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE topics SET name = ? WHERE id = ?', (name, topic_id))
    conn.commit()
    conn.close()

def delete_topic(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM topics WHERE id = ?', (topic_id,))
    conn.commit()
    conn.close()

# CRUD for lessons
def create_lesson(topic_id, teacher_name, video_url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO lessons (topic_id, teacher_name, video_url) VALUES (?, ?, ?)', (topic_id, teacher_name, video_url))
    lesson_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lesson_id

def get_lessons_by_topic(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, teacher_name, video_url FROM lessons WHERE topic_id = ? ORDER BY teacher_name', (topic_id,))
    lessons = cursor.fetchall()
    conn.close()
    return lessons

def update_lesson(lesson_id, teacher_name, video_url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE lessons SET teacher_name = ?, video_url = ? WHERE id = ?', (teacher_name, video_url, lesson_id))
    conn.commit()
    conn.close()

def delete_lesson(lesson_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
    conn.commit()
    conn.close()

# Additional helper functions
def get_category_by_id(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM categories WHERE id = ?', (category_id,))
    category = cursor.fetchone()
    conn.close()
    return category

def get_subcategory_by_id(subcategory_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, category_id, name FROM subcategories WHERE id = ?', (subcategory_id,))
    subcategory = cursor.fetchone()
    conn.close()
    return subcategory

def get_topic_by_id(topic_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, subcategory_id, name FROM topics WHERE id = ?', (topic_id,))
    topic = cursor.fetchone()
    conn.close()
    return topic

def get_lesson_by_id(lesson_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, topic_id, teacher_name, video_url FROM lessons WHERE id = ?', (lesson_id,))
    lesson = cursor.fetchone()
    conn.close()
    return lesson