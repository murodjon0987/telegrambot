# -*- coding: utf-8 -*-
import asyncio
import csv
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_database.sqlite")

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def _init_db_sync():
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Foydalanuvchilar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TEXT,
                last_active TEXT,
                greetings_count INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                referrer_id INTEGER DEFAULT 0,
                utm_source TEXT DEFAULT ''
            )
        """)
        
        # Schema migratsiyalari (agar avval yaratilgan bo'lsa)
        cursor.execute("PRAGMA table_info(users);")
        existing_cols = [row["name"] for row in cursor.fetchall()]
        if "is_banned" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0;")
        if "referrer_id" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0;")
        if "utm_source" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN utm_source TEXT DEFAULT '';")
        
        # 2. Foydalanuvchilar harakatlari jurnali (Activity Logs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                action TEXT,
                details TEXT,
                created_at TEXT
            )
        """)
        
        # 3. Yaratilgan tabriklar tarixi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS greetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                character TEXT,
                recipient_name TEXT,
                profession TEXT,
                sender_name TEXT,
                generated_text TEXT,
                created_at TEXT
            )
        """)
        
        # Indekslar (Tezkor qidiruv uchun)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON activity_logs(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_user_id ON activity_logs(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_greetings_user ON greetings(user_id);")
        conn.commit()

async def init_db():
    """Ma'lumotlar bazasini asinxron ishga tushirish."""
    await asyncio.to_thread(_init_db_sync)

def _upsert_user_sync(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str], referrer_id: int = 0, utm_source: str = ""):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute("""
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, last_active = ?
                WHERE user_id = ?
            """, (username, first_name, last_name, now_str, user_id))
        else:
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, created_at, last_active, greetings_count, is_banned, referrer_id, utm_source)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """, (user_id, username, first_name, last_name, now_str, now_str, referrer_id, utm_source))
        conn.commit()

async def upsert_user(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str], referrer_id: int = 0, utm_source: str = ""):
    """Foydalanuvchi ma'lumotlarini qo'shish yoki yangilash."""
    await asyncio.to_thread(_upsert_user_sync, user_id, username, first_name, last_name, referrer_id, utm_source)

def _is_user_banned_sync(user_id: int) -> bool:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return bool(row and row["is_banned"])

async def is_user_banned(user_id: int) -> bool:
    """Foydalanuvchi bloklanganligini tekshirish."""
    return await asyncio.to_thread(_is_user_banned_sync, user_id)

def _set_ban_status_sync(user_id: int, banned: bool):
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if banned else 0, user_id))
        conn.commit()

async def ban_user(user_id: int):
    """Foydalanuvchini bloklash."""
    await asyncio.to_thread(_set_ban_status_sync, user_id, True)

async def unban_user(user_id: int):
    """Foydalanuvchini blokdan chiqarish."""
    await asyncio.to_thread(_set_ban_status_sync, user_id, False)

def _log_activity_sync(user_id: int, username: Optional[str], full_name: str, action: str, details: str):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, full_name, action, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, full_name, action, details, now_str))
        
        # Foydalanuvchining last_active vaqtini yangilash
        cursor.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now_str, user_id))
        conn.commit()

async def log_activity(user_id: int, username: Optional[str], full_name: str, action: str, details: str):
    """Foydalanuvchining har bir harakatini bazaga yozish."""
    await asyncio.to_thread(_log_activity_sync, user_id, username, full_name, action, details)

def _save_greeting_sync(user_id: int, category: str, character: str, recipient_name: str, profession: str, sender_name: str, text: str):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO greetings (user_id, category, character, recipient_name, profession, sender_name, generated_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, category, character, recipient_name, profession, sender_name, text, now_str))
        
        cursor.execute("""
            UPDATE users SET greetings_count = greetings_count + 1, last_active = ? WHERE user_id = ?
        """, (now_str, user_id))
        conn.commit()

async def save_greeting(user_id: int, category: str, character: str, recipient_name: str, profession: str, sender_name: str, text: str):
    """Yaratilgan tabrikni arxivlash va foydalanuvchi hisoblagichini oshirish."""
    await asyncio.to_thread(_save_greeting_sync, user_id, category, character, recipient_name, profession, sender_name, text)

def _get_user_greetings_sync(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category, character, recipient_name, profession, sender_name, generated_text, created_at
            FROM greetings
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def get_user_greetings(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Foydalanuvchi yaratgan oxirgi tabriklarni olish."""
    return await asyncio.to_thread(_get_user_greetings_sync, user_id, limit)

def _get_top_stats_sync() -> Dict[str, Any]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # Eng mashhur obrazlar
        cursor.execute("""
            SELECT character, COUNT(*) as count 
            FROM greetings 
            WHERE character IS NOT NULL AND character != ''
            GROUP BY character 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_characters = [dict(row) for row in cursor.fetchall()]

        # Eng mashhur kasblar
        cursor.execute("""
            SELECT profession, COUNT(*) as count 
            FROM greetings 
            WHERE profession IS NOT NULL AND profession != ''
            GROUP BY profession 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_professions = [dict(row) for row in cursor.fetchall()]

        # Eng ko'p do'st taklif qilganlar
        cursor.execute("""
            SELECT referrer_id, COUNT(*) as ref_count 
            FROM users 
            WHERE referrer_id > 0 
            GROUP BY referrer_id 
            ORDER BY ref_count DESC 
            LIMIT 5
        """)
        top_referrers = [dict(row) for row in cursor.fetchall()]

        return {
            "top_characters": top_characters,
            "top_professions": top_professions,
            "top_referrers": top_referrers
        }

async def get_top_stats() -> Dict[str, Any]:
    """Obrazlar va kasblar bo'yicha eng mashhur statistikani olish."""
    return await asyncio.to_thread(_get_top_stats_sync)

def _cleanup_old_logs_sync(days: int = 30) -> int:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM activity_logs 
            WHERE created_at < datetime('now', '-' || ? || ' days')
        """, (days,))
        deleted = cursor.rowcount
        conn.commit()
        return deleted

async def cleanup_old_logs(days: int = 30) -> int:
    """Eskirgan loglarni tozalash (xotirani tejash uchun)."""
    return await asyncio.to_thread(_cleanup_old_logs_sync, days)

def _get_statistics_sync() -> Dict[str, Any]:
    today_str = datetime.now().strftime("%Y-%m-%d")
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # Jami foydalanuvchilar
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Bugun qo'shilganlar
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (f"{today_str}%",))
        today_users = cursor.fetchone()[0]
        
        # Bugun faol bo'lganlar
        cursor.execute("SELECT COUNT(*) FROM users WHERE last_active LIKE ?", (f"{today_str}%",))
        active_today = cursor.fetchone()[0]
        
        # Jami tabriklar
        cursor.execute("SELECT COUNT(*) FROM greetings")
        total_greetings = cursor.fetchone()[0]
        
        # Bugun yaratilgan tabriklar
        cursor.execute("SELECT COUNT(*) FROM greetings WHERE created_at LIKE ?", (f"{today_str}%",))
        today_greetings = cursor.fetchone()[0]
        
        # Jami jurnal harakatlari
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        total_logs = cursor.fetchone()[0]
        
        # Bloklanganlar
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = cursor.fetchone()[0]
        
        return {
            "total_users": total_users,
            "today_users": today_users,
            "active_today": active_today,
            "total_greetings": total_greetings,
            "today_greetings": today_greetings,
            "total_logs": total_logs,
            "banned_users": banned_users
        }

async def get_statistics() -> Dict[str, Any]:
    """Admin uchun umumiy statistikani olish."""
    return await asyncio.to_thread(_get_statistics_sync)

def _get_recent_logs_sync(limit: int = 15) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, full_name, action, details, created_at
            FROM activity_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def get_recent_logs(limit: int = 15) -> List[Dict[str, Any]]:
    """Oxirgi harakatlar jurnalini olish."""
    return await asyncio.to_thread(_get_recent_logs_sync, limit)

def _get_recent_users_sync(limit: int = 10) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, first_name, last_name, created_at, last_active, greetings_count, is_banned
            FROM users
            ORDER BY last_active DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def get_recent_users(limit: int = 10) -> List[Dict[str, Any]]:
    """Oxirgi faol foydalanuvchilar ro'yxati."""
    return await asyncio.to_thread(_get_recent_users_sync, limit)

def _get_user_info_sync(user_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return None
        
        user_dict = dict(user_row)
        
        # Oxirgi 5 ta harakati
        cursor.execute("""
            SELECT action, details, created_at FROM activity_logs
            WHERE user_id = ? ORDER BY id DESC LIMIT 5
        """, (user_id,))
        user_dict["recent_activities"] = [dict(r) for r in cursor.fetchall()]
        
        # Oxirgi 5 ta yaratgan tabriki
        cursor.execute("""
            SELECT category, character, recipient_name, profession, sender_name, created_at
            FROM greetings WHERE user_id = ? ORDER BY id DESC LIMIT 5
        """, (user_id,))
        user_dict["recent_greetings"] = [dict(r) for r in cursor.fetchall()]
        
        return user_dict

async def get_user_info(user_id: int) -> Optional[Dict[str, Any]]:
    """Foydalanuvchi haqida to'liq hisobot."""
    return await asyncio.to_thread(_get_user_info_sync, user_id)

def _get_all_user_ids_sync() -> List[int]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
        rows = cursor.fetchall()
        return [row[0] for row in rows]

async def get_all_user_ids() -> List[int]:
    """Barcha faol (bloklanmagan) foydalanuvchilar ID ro'yxati (Rassilka uchun)."""
    return await asyncio.to_thread(_get_all_user_ids_sync)

def _export_users_csv_sync(filepath: str) -> str:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, first_name, last_name, created_at, last_active, greetings_count, is_banned, referrer_id, utm_source
            FROM users ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["User ID", "Username", "Ismi", "Familiyasi", "Qo'shilgan vaqti", "Oxirgi faolligi", "Tabriklar soni", "Bloklangan", "Taklif qilgan ID", "UTM Manba"])
            for r in rows:
                writer.writerow([
                    r["user_id"], 
                    r["username"] or "", 
                    r["first_name"] or "", 
                    r["last_name"] or "", 
                    r["created_at"], 
                    r["last_active"], 
                    r["greetings_count"],
                    r["is_banned"],
                    r["referrer_id"],
                    r["utm_source"]
                ])
                
    return filepath

async def export_users_csv(filepath: str) -> str:
    """Foydalanuvchilar ro'yxatini CSV fayl qilib eksport qilish."""
    return await asyncio.to_thread(_export_users_csv_sync, filepath)
