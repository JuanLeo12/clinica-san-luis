#!/usr/bin/env python3
"""Add English columns to Spanish tables"""
import sqlite3

conn = sqlite3.connect('clinic_app.sqlite3')
c = conn.cursor()

# Add English columns to consultorios
c.execute('PRAGMA table_info(consultorios)')
cols = [col[1] for col in c.fetchall()]

if 'name' not in cols:
    c.execute('ALTER TABLE consultorios ADD COLUMN name TEXT')
    c.execute('UPDATE consultorios SET name = nombre WHERE name IS NULL')
    print('Added name column')

conn.commit()
conn.close()
print('Done')