#!/usr/bin/env python3
"""Fix v_consultorios view - correct column mapping"""
import sqlite3

conn = sqlite3.connect('clinic_app.sqlite3')

# Drop and recreate with correct columns
sql = """
DROP VIEW IF EXISTS v_consultorios;
CREATE VIEW v_consultorios AS
SELECT
    id AS id,
    nombre AS nombre,
    piso AS piso,
    equipo AS equipo,
    activo AS activo,
    created_at AS fecha_creacion
FROM consultorios;
"""
conn.executescript(sql)

# Add active column to base table
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(consultorios)")
cols = [c[1] for c in cursor.fetchall()]
if 'active' not in cols:
    cursor.execute("ALTER TABLE consultorios ADD COLUMN active INTEGER DEFAULT 1")
    cursor.execute("UPDATE consultorios SET active = activo WHERE active IS NULL")
    conn.commit()
    print("Added active column")
else:
    print("active column already exists")

conn.close()
print("Fixed v_consultorios view!")