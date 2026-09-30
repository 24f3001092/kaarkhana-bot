
import sqlite3, json, time
from pathlib import Path
from ..config import DATABASE_PATH

def connect():
    con=sqlite3.connect(DATABASE_PATH)
    con.row_factory=sqlite3.Row
    return con

def init_db():
    con=connect()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS conversations(
      id TEXT PRIMARY KEY, created_at REAL NOT NULL, updated_at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL,
      role TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tasks(
      id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, prompt TEXT,
      status TEXT NOT NULL, analysis_json TEXT, plan_json TEXT,
      answer_json TEXT, created_at REAL NOT NULL
    );
    """)
    con.commit(); con.close()

def ensure_conversation(cid):
    now=time.time()
    con=connect()
    con.execute("INSERT OR IGNORE INTO conversations(id,created_at,updated_at) VALUES(?,?,?)",(cid,now,now))
    con.execute("UPDATE conversations SET updated_at=? WHERE id=?",(now,cid))
    con.commit(); con.close()

def add_message(cid, role, content):
    ensure_conversation(cid)
    con=connect()
    con.execute("INSERT INTO messages(conversation_id,role,content,created_at) VALUES(?,?,?,?)",(cid,role,content,time.time()))
    con.commit(); con.close()

def recent_messages(cid, limit=6):
    con=connect()
    rows=con.execute("SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?",(cid,limit)).fetchall()
    con.close()
    return list(reversed([dict(r) for r in rows]))

def save_task(task_id,cid,prompt,status,analysis=None,plan=None,answer=None):
    con=connect()
    con.execute("""INSERT OR REPLACE INTO tasks
      (id,conversation_id,prompt,status,analysis_json,plan_json,answer_json,created_at)
      VALUES(?,?,?,?,?,?,?,?)""",
      (task_id,cid,prompt,status,
       json.dumps(analysis,ensure_ascii=False) if analysis is not None else None,
       json.dumps(plan,ensure_ascii=False) if plan is not None else None,
       json.dumps(answer,ensure_ascii=False) if answer is not None else None,
       time.time()))
    con.commit(); con.close()
