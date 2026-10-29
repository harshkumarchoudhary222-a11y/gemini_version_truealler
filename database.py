from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import aiosqlite

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, path: str = "bot_data.db"):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users(
              user_id INTEGER PRIMARY KEY, username TEXT NOT NULL DEFAULT '',
              first_name TEXT NOT NULL DEFAULT 'User', is_premium INTEGER NOT NULL DEFAULT 0,
              credits INTEGER NOT NULL DEFAULT 5, daily_used INTEGER NOT NULL DEFAULT 0,
              daily_reset TEXT NOT NULL, ads_viewed INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lookup_events(
              id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
              phone_number TEXT NOT NULL, success INTEGER NOT NULL, created_at TEXT NOT NULL
            );
            """)
            await db.commit()

    async def get_or_create_user(self, user_id: int, username: str|None, first_name: str|None) -> dict[str,Any]:
        now=utc_now()
        async with aiosqlite.connect(self.path) as db:
            db.row_factory=aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
                row=await cur.fetchone()
            if row:
                await db.execute("UPDATE users SET username=?,first_name=?,updated_at=? WHERE user_id=?",
                                  (username or "", first_name or "User", now, user_id))
                await db.commit()
                return dict(row)
            await db.execute("""INSERT INTO users
                (user_id,username,first_name,daily_reset,created_at,updated_at)
                VALUES(?,?,?,?,?,?)""",
                (user_id,username or "",first_name or "User",now[:10],now,now))
            await db.commit()
            return {"user_id":user_id,"username":username or "","first_name":first_name or "User",
                    "is_premium":0,"credits":5,"daily_used":0,"daily_reset":now[:10],
                    "ads_viewed":0,"created_at":now,"updated_at":now}

    async def consume_lookup(self,user_id:int,is_premium:bool,daily_limit:int)->bool:
        today=utc_now()[:10]
        async with aiosqlite.connect(self.path) as db:
            await db.execute("BEGIN IMMEDIATE")
            async with db.execute("SELECT credits,daily_used,daily_reset FROM users WHERE user_id=?",(user_id,)) as cur:
                row=await cur.fetchone()
            if not row:
                await db.rollback(); return False
            credits,daily_used,daily_reset=row
            if daily_reset != today:
                daily_used=0
                await db.execute("UPDATE users SET daily_used=0,daily_reset=? WHERE user_id=?",(today,user_id))
            if is_premium:
                await db.commit(); return True
            if daily_used < daily_limit:
                await db.execute("UPDATE users SET daily_used=daily_used+1,updated_at=? WHERE user_id=?",(utc_now(),user_id))
                await db.commit(); return True
            if credits <= 0:
                await db.commit(); return False
            await db.execute("UPDATE users SET credits=credits-1,updated_at=? WHERE user_id=?",(utc_now(),user_id))
            await db.commit(); return True

    async def add_credits(self,user_id:int,amount:int)->None:
        if amount<=0:return
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET credits=credits+?,updated_at=? WHERE user_id=?",(amount,utc_now(),user_id))
            await db.commit()

    async def set_premium(self,user_id:int,enabled:bool)->None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET is_premium=?,updated_at=? WHERE user_id=?",(int(enabled),utc_now(),user_id))
            await db.commit()

    async def record_lookup(self,user_id:int,phone_number:str,success:bool)->None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO lookup_events(user_id,phone_number,success,created_at) VALUES(?,?,?,?)",
                             (user_id,phone_number,int(success),utc_now()))
            await db.commit()
