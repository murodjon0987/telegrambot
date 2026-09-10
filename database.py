# -*- coding: utf-8 -*-
import asyncio
import csv
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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
                utm_source TEXT DEFAULT '',
                points INTEGER DEFAULT 0
            )
        """)
        
        # Schema migratsiyalari (ustunlar mavjudligini tekshirish)
        cursor.execute("PRAGMA table_info(users);")
        existing_cols = [row["name"] for row in cursor.fetchall()]
        if "is_banned" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0;")
        if "referrer_id" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0;")
        if "utm_source" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN utm_source TEXT DEFAULT '';")
        if "points" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0;")
        
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_points ON users(points);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON activity_logs(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_user_id ON activity_logs(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_greetings_user ON greetings(user_id);")
        conn.commit()

async def init_db():
    """Ma'lumotlar bazasini asinxron ishga tushirish."""
    await asyncio.to_thread(_init_db_sync)

def _upsert_user_sync(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str], referrer_id: int = 0, utm_source: str = "") -> Tuple[bool, int]:
    """
    Foydalanuvchini qo'shish yoki yangilash.
    Qaytaradi: (is_new_user: bool, bonus_referrer_id: int)
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bonus_referrer_id = 0
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
            conn.commit()
            return False, 0
        else:
            # Yangi foydalanuvchi!
            # Agar referral mavjud bo'lsa va o'zini o'zi taklif qilmagan bo'lsa
            actual_ref = referrer_id if (referrer_id > 0 and referrer_id != user_id) else 0
            
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, created_at, last_active, greetings_count, is_banned, referrer_id, utm_source, points)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?, 5)
            """, (user_id, username, first_name, last_name, now_str, now_str, actual_ref, utm_source))
            
            # Yangi foydalanuvchiga boshlang'ich +5 ball bonus!
            if actual_ref > 0:
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (actual_ref,))
                ref_exists = cursor.fetchone()
                if ref_exists:
                    # Referrerga +10 ball beriladi!
                    cursor.execute("UPDATE users SET points = points + 10 WHERE user_id = ?", (actual_ref,))
                    cursor.execute("""
                        INSERT INTO activity_logs (user_id, username, full_name, action, details, created_at)
                        VALUES (?, '', 'Referral System', 'REF_BONUS', ?, ?)
                    """, (actual_ref, f"Do'st taklif qildi (+10 ball, yangi foydalanuvchi: {user_id})", now_str))
                    bonus_referrer_id = actual_ref

            conn.commit()
            return True, bonus_referrer_id

async def upsert_user(user_id: int, username: Optional[str], first_name: str, last_name: Optional[str], referrer_id: int = 0, utm_source: str = "") -> Tuple[bool, int]:
    """Foydalanuvchi ma'lumotlarini qo'shish yoki yangilash."""
    return await asyncio.to_thread(_upsert_user_sync, user_id, username, first_name, last_name, referrer_id, utm_source)

def _add_user_points_sync(user_id: int, points: int, reason: str = ""):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET points = points + ?, last_active = ? WHERE user_id = ?", (points, now_str, user_id))
        if reason:
            cursor.execute("""
                INSERT INTO activity_logs (user_id, username, full_name, action, details, created_at)
                VALUES (?, '', 'Ball Tizimi', 'ADD_POINTS', ?, ?)
            """, (user_id, f"+{points} ball ({reason})", now_str))
        conn.commit()

async def add_user_points(user_id: int, points: int, reason: str = ""):
    """Foydalanuvchiga ball qo'shish."""
    await asyncio.to_thread(_add_user_points_sync, user_id, points, reason)

def _get_user_profile_sync(user_id: int) -> Dict[str, Any]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return {}
        
        user_dict = dict(user_row)
        
        # Taklif qilgan do'stlari soni
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        ref_count = cursor.fetchone()[0]
        user_dict["ref_count"] = ref_count

        points = user_dict.get("points", 0)
        
        # Daraja / Unvon hisoblash
        if points < 20:
            rank_title = "🥉 Oddiy Mehmon"
            next_rank = "🥈 Mahalla Faoli"
            needed = 20 - points
        elif points < 50:
            rank_title = "🥈 Mahalla Faoli"
            next_rank = "🥇 Saxiy Homiy"
            needed = 50 - points
        elif points < 100:
            rank_title = "🥇 Saxiy Homiy"
            next_rank = "👑 Toshkent Avtoriteti (VIP)"
            needed = 100 - points
        else:
            rank_title = "👑 Toshkent Avtoriteti (VIP)"
            next_rank = "🏆 Maksimal Daraja!"
            needed = 0

        user_dict["rank_title"] = rank_title
        user_dict["next_rank"] = next_rank
        user_dict["points_needed"] = needed
        
        return user_dict

async def get_user_profile(user_id: int) -> Dict[str, Any]:
    """Foydalanuvchi profil ma'lumotlari, ballari va unvonini olish."""
    return await asyncio.to_thread(_get_user_profile_sync, user_id)

def _get_leaderboard_sync(limit: int = 10) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, first_name, last_name, points, greetings_count,
                   (SELECT COUNT(*) FROM users u2 WHERE u2.referrer_id = users.user_id) as ref_count
            FROM users
            WHERE is_banned = 0
            ORDER BY points DESC, ref_count DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

async def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """Eng ko'p ball to'plagan Top 10 peshqadamlar ro'yxati."""
    return await asyncio.to_thread(_get_leaderboard_sync, limit)

def _can_claim_daily_fortune_sync(user_id: int) -> bool:
    today_str = datetime.now().strftime("%Y-%m-%d")
    action_key = f"FORTUNE_{today_str}"
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM activity_logs 
            WHERE user_id = ? AND action = ?
            LIMIT 1
        """, (user_id, action_key))
        return cursor.fetchone() is None

async def can_claim_daily_fortune(user_id: int) -> bool:
    """Foydalanuvchi bugun o'z bashoratini olgan-olmaganligini tekshirish."""
    return await asyncio.to_thread(_can_claim_daily_fortune_sync, user_id)

def _claim_daily_fortune_sync(user_id: int):
    today_str = datetime.now().strftime("%Y-%m-%d")
    action_key = f"FORTUNE_{today_str}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_logs (user_id, username, full_name, action, details, created_at)
            VALUES (?, '', 'Kunlik Bashorat', ?, 'Bugungi kunlik bashorat olindi (+1 ball)', ?)
        """, (user_id, action_key, now_str))
        cursor.execute("UPDATE users SET points = points + 1, last_active = ? WHERE user_id = ?", (now_str, user_id))
        conn.commit()

async def claim_daily_fortune(user_id: int):
    """Kunlik bashorat bonusini berish va qayd qilish."""
    await asyncio.to_thread(_claim_daily_fortune_sync, user_id)

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
        
        cursor.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now_str, user_id))
        conn.commit()

async def log_activity(user_id: int, username: Optional[str], full_name: str, action: str, details: str):
    """Foydalanuvchining har bir harakatini bazaga yozish."""
    await asyncio.to_thread(_log_activity_sync, user_id, username, full_name, action, details)

def _save_greeting_sync(user_id: int, category: str, character: str, recipient_name: str, profession: str, sender_name: str, text: str) -> int:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO greetings (user_id, category, character, recipient_name, profession, sender_name, generated_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, category, character, recipient_name, profession, sender_name, text, now_str))
        greeting_id = cursor.lastrowid or 0
        
        # Tabrik yaratganda +2 ball beriladi!
        cursor.execute("""
            UPDATE users SET greetings_count = greetings_count + 1, points = points + 2, last_active = ? WHERE user_id = ?
        """, (now_str, user_id))
        conn.commit()
        return greeting_id

async def save_greeting(user_id: int, category: str, character: str, recipient_name: str, profession: str, sender_name: str, text: str) -> int:
    """Yaratilgan tabrikni arxivlash va foydalanuvchi hisoblagichini oshirish."""
    return await asyncio.to_thread(_save_greeting_sync, user_id, category, character, recipient_name, profession, sender_name, text)

def _get_greeting_by_id_sync(greeting_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, category, character, recipient_name, profession, sender_name, generated_text, created_at
            FROM greetings WHERE id = ?
        """, (greeting_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

async def get_greeting_by_id(greeting_id: int) -> Optional[Dict[str, Any]]:
    """ID bo'yicha bitta tabrikni olish."""
    return await asyncio.to_thread(_get_greeting_by_id_sync, greeting_id)

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
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (f"{today_str}%",))
        today_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE last_active LIKE ?", (f"{today_str}%",))
        active_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM greetings")
        total_greetings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM greetings WHERE created_at LIKE ?", (f"{today_str}%",))
        today_greetings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        total_logs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(points) FROM users")
        total_points = cursor.fetchone()[0] or 0
        
        return {
            "total_users": total_users,
            "today_users": today_users,
            "active_today": active_today,
            "total_greetings": total_greetings,
            "today_greetings": today_greetings,
            "total_logs": total_logs,
            "banned_users": banned_users,
            "total_points": total_points
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
            SELECT user_id, username, first_name, last_name, created_at, last_active, greetings_count, is_banned, points
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
        
        # Taklif qilganlari
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        user_dict["ref_count"] = cursor.fetchone()[0]
        
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
            SELECT user_id, username, first_name, last_name, created_at, last_active, greetings_count, is_banned, referrer_id, utm_source, points
            FROM users ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["User ID", "Username", "Ismi", "Familiyasi", "Qo'shilgan vaqti", "Oxirgi faolligi", "Tabriklar soni", "Bloklangan", "Taklif qilgan ID", "UTM Manba", "Ballar"])
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
                    r["utm_source"],
                    r["points"]
                ])
                
    return filepath

async def export_users_csv(filepath: str) -> str:
    """Foydalanuvchilar ro'yxatini CSV fayl qilib eksport qilish."""
    return await asyncio.to_thread(_export_users_csv_sync, filepath)
