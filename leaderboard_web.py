# -*- coding: utf-8 -*-
import html
from typing import Any, Dict, List

def render_leaderboard_html(
    entries: List[Dict[str, Any]],
    stats: Dict[str, Any],
    bot_username: str = "parodiya_tabrik_uzbot"
) -> str:
    """
    Forbes VIP / Top Boyvachchalar shon-sharaf taxtasi veb-sahifasini
    zamonaviy, ultra-premium va responsiv HTML/CSS formatida generatsiya qilish.
    """
    total_participants = stats.get("total_participants", len(entries))
    total_donations = stats.get("total_donations", sum(e.get("amount", 0) for e in entries))
    highest_donation = stats.get("highest_donation", entries[0].get("amount", 0) if entries else 0)

    # Top 3 ajratib olish
    top_1 = entries[0] if len(entries) > 0 else None
    top_2 = entries[1] if len(entries) > 1 else None
    top_3 = entries[2] if len(entries) > 2 else None
    rest_entries = entries[3:] if len(entries) > 3 else []

    # Helper rasm manzilini olish
    def get_img_src(entry: Any) -> str:
        if not entry:
            return "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80"
        filename = entry.get("image_filename", "")
        if filename:
            return f"/photo/{filename}"
        return "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80"

    # Rest entries HTML
    rows_html = ""
    for idx, item in enumerate(rest_entries, start=4):
        img_src = get_img_src(item)
        name_esc = html.escape(item.get("friend_name", "Noma'lum"))
        title_esc = html.escape(item.get("friend_title", "Boyvachcha"))
        amount = item.get("amount", 0)
        date_str = item.get("created_at", "")[:10]
        
        rows_html += f"""
        <tr class="table-row">
            <td class="rank-col">
                <span class="rank-badge">#{idx}</span>
            </td>
            <td class="user-col">
                <div class="avatar-wrap">
                    <img src="{img_src}" alt="{name_esc}" class="user-avatar" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80'">
                </div>
                <div class="user-meta">
                    <span class="user-name">{name_esc}</span>
                    <span class="user-title">{title_esc}</span>
                </div>
            </td>
            <td class="amount-col">
                <span class="amount-val">{amount:,} so'm</span>
            </td>
            <td class="date-col">
                <span class="date-val">{date_str}</span>
            </td>
        </tr>
        """

    if not rows_html and not top_1:
        empty_state_html = """
        <div class="empty-box">
            <div class="empty-icon">👑</div>
            <h3>Hozircha reyting bo'sh!</h3>
            <p>Birinchi bo'lib do'stingizni saytga joylang va #1 o'rinni egallang!</p>
            <a href="https://t.me/parodiya_tabrik_uzbot?start=top_boyvachcha" class="btn-primary" target="_blank">
                🚀 Birinchi bo'lib qo'shish
            </a>
        </div>
        """
    else:
        empty_state_html = ""

    html_content = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 FORBES UZBEKISTAN — Top Boyvachchalar & Do'stlar Reytingi</title>
    
    <!-- Meta Teglar (SEO va Telegram Preview) -->
    <meta name="description" content="O'zbekistondagi eng saxiy do'stlar va top boyvachchalar shon-sharaf taxtasi! Do'stingizni #1 o'ringa chiqaring.">
    <meta property="og:title" content="👑 FORBES UZBEKISTAN — Jonli Reyting">
    <meta property="og:description" content="Kim do'sti uchun eng ko'p pul tashladi? Jonli reytingni ko'ring yoki o'zingiznikini qo'shing!">
    <meta property="og:image" content="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&w=1200&q=80">
    <meta property="og:type" content="website">

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">

    <style>
        :root {{
            --bg-dark: #07080d;
            --bg-card: rgba(19, 23, 37, 0.75);
            --bg-card-hover: rgba(27, 33, 53, 0.9);
            --gold-primary: #fbbf24;
            --gold-secondary: #f59e0b;
            --gold-glow: rgba(245, 158, 11, 0.35);
            --silver: #cbd5e1;
            --bronze: #d97706;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-gold: rgba(251, 191, 36, 0.25);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        body {{
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(circle at 50% 0%, rgba(245, 158, 11, 0.15) 0%, transparent 60%),
                radial-gradient(circle at 10% 30%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 90% 80%, rgba(234, 179, 8, 0.08) 0%, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }}

        /* Header & Hero */
        header {{
            text-align: center;
            padding: 50px 20px 30px;
            position: relative;
        }}

        .badge-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 18px;
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid var(--border-gold);
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--gold-primary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
            box-shadow: 0 0 20px var(--gold-glow);
            animation: pulse-glow 3s infinite alternate;
        }}

        @keyframes pulse-glow {{
            0% {{ box-shadow: 0 0 15px rgba(245, 158, 11, 0.2); }}
            100% {{ box-shadow: 0 0 25px rgba(245, 158, 11, 0.5); }}
        }}

        h1.title {{
            font-size: clamp(2.2rem, 5vw, 3.8rem);
            font-weight: 900;
            letter-spacing: -0.5px;
            line-height: 1.15;
            background: linear-gradient(135deg, #ffffff 20%, #fde68a 60%, #f59e0b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 14px;
        }}

        p.subtitle {{
            font-size: clamp(1rem, 2vw, 1.25rem);
            color: var(--text-muted);
            max-width: 650px;
            margin: 0 auto 28px;
            line-height: 1.6;
        }}

        /* Stats Bar */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            max-width: 800px;
            margin: 0 auto 36px;
            padding: 0 16px;
        }}

        .stat-card {{
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: 20px;
            padding: 18px;
            text-align: center;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-4px);
            border-color: var(--border-gold);
        }}

        .stat-num {{
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--gold-primary);
            display: block;
            margin-bottom: 4px;
        }}

        .stat-label {{
            font-size: 0.82rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}

        /* Action Buttons */
        .hero-actions {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 14px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }}

        .btn-primary {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: #000;
            font-size: 1.05rem;
            font-weight: 800;
            padding: 16px 32px;
            border-radius: 999px;
            text-decoration: none;
            box-shadow: 0 10px 25px rgba(245, 158, 11, 0.4);
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }}

        .btn-primary:hover {{
            transform: scale(1.04) translateY(-2px);
            box-shadow: 0 15px 35px rgba(245, 158, 11, 0.6);
            color: #000;
        }}

        .btn-secondary {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            font-size: 1rem;
            font-weight: 600;
            padding: 15px 28px;
            border-radius: 999px;
            text-decoration: none;
            border: 1px solid var(--border-glass);
            transition: all 0.3s ease;
        }}

        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
            color: #fff;
        }}

        /* Container */
        .main-container {{
            max-width: 1100px;
            width: 100%;
            margin: 0 auto;
            padding: 0 20px 80px;
            flex: 1;
        }}

        /* Podium Layout */
        .podium-wrap {{
            display: grid;
            grid-template-columns: 1fr 1.15fr 1fr;
            gap: 20px;
            align-items: end;
            margin: 40px auto 60px;
            max-width: 950px;
        }}

        .podium-card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 28px;
            padding: 28px 20px;
            text-align: center;
            position: relative;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border: 1px solid var(--border-glass);
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .podium-card:hover {{
            transform: translateY(-8px);
        }}

        /* 1-O'rin (Chempion) */
        .podium-1 {{
            border-color: rgba(251, 191, 36, 0.5);
            background: linear-gradient(180deg, rgba(245, 158, 11, 0.18) 0%, rgba(19, 23, 37, 0.85) 60%);
            box-shadow: 0 15px 40px rgba(245, 158, 11, 0.2);
            order: 2;
            padding: 38px 24px;
        }}

        .podium-1 .avatar-ring {{
            border: 4px solid var(--gold-primary);
            box-shadow: 0 0 30px var(--gold-glow);
            width: 130px;
            height: 130px;
        }}

        .podium-2 {{
            order: 1;
            border-color: rgba(203, 213, 225, 0.25);
        }}

        .podium-2 .avatar-ring {{
            border: 3px solid var(--silver);
            width: 105px;
            height: 105px;
        }}

        .podium-3 {{
            order: 3;
            border-color: rgba(217, 119, 6, 0.25);
        }}

        .podium-3 .avatar-ring {{
            border: 3px solid var(--bronze);
            width: 105px;
            height: 105px;
        }}

        .avatar-ring {{
            border-radius: 50%;
            overflow: hidden;
            position: relative;
            margin-bottom: 16px;
            background: #1e293b;
        }}

        .avatar-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .crown-icon {{
            font-size: 2.2rem;
            position: absolute;
            top: -24px;
            left: 50%;
            transform: translateX(-50%);
            filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5));
            animation: float-crown 3s ease-in-out infinite alternate;
        }}

        @keyframes float-crown {{
            0% {{ transform: translateX(-50%) translateY(0); }}
            100% {{ transform: translateX(-50%) translateY(-6px); }}
        }}

        .place-tag {{
            font-size: 0.8rem;
            font-weight: 800;
            padding: 4px 14px;
            border-radius: 999px;
            text-transform: uppercase;
            margin-bottom: 12px;
            display: inline-block;
        }}

        .tag-1 {{ background: #f59e0b; color: #000; }}
        .tag-2 {{ background: #94a3b8; color: #000; }}
        .tag-3 {{ background: #d97706; color: #fff; }}

        .podium-name {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #fff;
            margin-bottom: 4px;
            word-break: break-word;
        }}

        .podium-title {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 14px;
            font-weight: 600;
        }}

        .podium-amount {{
            font-size: 1.2rem;
            font-weight: 900;
            color: var(--gold-primary);
            background: rgba(245, 158, 11, 0.12);
            padding: 6px 16px;
            border-radius: 12px;
            border: 1px solid var(--border-gold);
            margin-top: auto;
        }}

        /* Search & Table Header */
        .table-section {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 28px;
            border: 1px solid var(--border-glass);
            padding: 30px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        }}

        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 24px;
        }}

        .section-title {{
            font-size: 1.4rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .search-input {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-glass);
            border-radius: 999px;
            padding: 12px 22px;
            color: #fff;
            font-size: 0.95rem;
            width: 100%;
            max-width: 280px;
            outline: none;
            transition: border-color 0.3s ease;
        }}

        .search-input:focus {{
            border-color: var(--gold-primary);
        }}

        /* Table */
        .leaderboard-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 10px;
        }}

        .leaderboard-table th {{
            color: var(--text-muted);
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 12px 18px;
            text-align: left;
        }}

        .table-row {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            transition: all 0.2s ease;
        }}

        .table-row:hover {{
            background: rgba(255, 255, 255, 0.07);
            transform: translateX(4px);
        }}

        .table-row td {{
            padding: 16px 18px;
            vertical-align: middle;
        }}

        .table-row td:first-child {{
            border-top-left-radius: 16px;
            border-bottom-left-radius: 16px;
        }}

        .table-row td:last-child {{
            border-top-right-radius: 16px;
            border-bottom-right-radius: 16px;
        }}

        .rank-badge {{
            font-weight: 800;
            color: var(--text-muted);
            font-size: 1.05rem;
        }}

        .user-col {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .avatar-wrap {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            overflow: hidden;
            background: #1e293b;
            flex-shrink: 0;
            border: 2px solid var(--border-glass);
        }}

        .user-avatar {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .user-meta {{
            display: flex;
            flex-direction: column;
        }}

        .user-name {{
            font-weight: 700;
            font-size: 1.05rem;
            color: #fff;
        }}

        .user-title {{
            font-size: 0.82rem;
            color: var(--text-muted);
        }}

        .amount-val {{
            font-weight: 800;
            color: var(--gold-primary);
            font-size: 1.05rem;
        }}

        .date-val {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        /* Empty State */
        .empty-box {{
            text-align: center;
            padding: 60px 20px;
        }}

        .empty-icon {{
            font-size: 4rem;
            margin-bottom: 16px;
        }}

        .empty-box h3 {{
            font-size: 1.5rem;
            margin-bottom: 8px;
        }}

        .empty-box p {{
            color: var(--text-muted);
            margin-bottom: 24px;
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 40px 20px;
            border-top: 1px solid var(--border-glass);
            color: var(--text-muted);
            font-size: 0.9rem;
            background: rgba(7, 8, 13, 0.8);
        }}

        footer a {{
            color: var(--gold-primary);
            text-decoration: none;
            font-weight: 600;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .podium-wrap {{
                grid-template-columns: 1fr;
                gap: 16px;
            }}

            .podium-1 {{
                order: 1;
            }}
            .podium-2 {{
                order: 2;
            }}
            .podium-3 {{
                order: 3;
            }}

            .section-header {{
                flex-direction: column;
                align-items: stretch;
            }}

            .search-input {{
                max-width: 100%;
            }}

            .date-col {{
                display: none;
            }}
        }}
    </style>
</head>
<body>

    <header>
        <div class="badge-pill">
            <span>✨</span> O'zbekistonning Eng Saxiy Insonlari
        </div>
        <h1 class="title">👑 FORBES UZBEKISTAN</h1>
        <p class="subtitle">
            Do'stini eng ko'p qo'llab-quvvatlagan, qadriga yetgan va pul o'tkazgan top boyvachchalar shon-sharaf taxtasi!
        </p>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-num">{total_participants} ta</span>
                <span class="stat-label">Jami Boyvachchalar</span>
            </div>
            <div class="stat-card">
                <span class="stat-num">{highest_donation:,} so'm</span>
                <span class="stat-label">#1 O'rin Rekordi</span>
            </div>
            <div class="stat-card">
                <span class="stat-num">{total_donations:,} so'm</span>
                <span class="stat-label">Jami Kiritilgan Pul</span>
            </div>
        </div>

        <div class="hero-actions">
            <a href="https://t.me/{bot_username}?start=top_boyvachcha" class="btn-primary" target="_blank">
                🚀 Do'stingizni #1 O'ringa Chiqaring
            </a>
            <button class="btn-secondary" onclick="shareLeaderboard()">
                📲 Ulashish
            </button>
        </div>
    </header>

    <main class="main-container">
"""

    # Top 3 Podium mavjud bo'lsa render qilamiz
    if top_1 or top_2 or top_3:
        p1_img = get_img_src(top_1) if top_1 else ""
        p1_name = html.escape(top_1.get("friend_name", "Bo'sh")) if top_1 else "Bo'sh"
        p1_title = html.escape(top_1.get("friend_title", "Unvon")) if top_1 else "Hali o'rin bo'sh"
        p1_amt = f"{top_1.get('amount', 0):,} so'm" if top_1 else "0 so'm"

        p2_img = get_img_src(top_2) if top_2 else ""
        p2_name = html.escape(top_2.get("friend_name", "Bo'sh")) if top_2 else "Bo'sh"
        p2_title = html.escape(top_2.get("friend_title", "Unvon")) if top_2 else "Hali o'rin bo'sh"
        p2_amt = f"{top_2.get('amount', 0):,} so'm" if top_2 else "0 so'm"

        p3_img = get_img_src(top_3) if top_3 else ""
        p3_name = html.escape(top_3.get("friend_name", "Bo'sh")) if top_3 else "Bo'sh"
        p3_title = html.escape(top_3.get("friend_title", "Unvon")) if top_3 else "Hali o'rin bo'sh"
        p3_amt = f"{top_3.get('amount', 0):,} so'm" if top_3 else "0 so'm"

        html_content += f"""
        <section class="podium-wrap">
            <!-- 2-O'RIN (KUMUSH) -->
            <div class="podium-card podium-2">
                <div class="avatar-ring">
                    <img src="{p2_img}" alt="{p2_name}" class="avatar-img" onerror="this.src='https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80'">
                </div>
                <span class="place-tag tag-2">🥈 2-O'RIN</span>
                <h3 class="podium-name">{p2_name}</h3>
                <span class="podium-title">{p2_title}</span>
                <span class="podium-amount">{p2_amt}</span>
            </div>

            <!-- 1-O'RIN (OLTIN CHEMPION) -->
            <div class="podium-card podium-1">
                <div class="crown-icon">👑</div>
                <div class="avatar-ring">
                    <img src="{p1_img}" alt="{p1_name}" class="avatar-img" onerror="this.src='https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=250&q=80'">
                </div>
                <span class="place-tag tag-1">🥇 1-O'RIN (QIROL)</span>
                <h3 class="podium-name">{p1_name}</h3>
                <span class="podium-title">{p1_title}</span>
                <span class="podium-amount">{p1_amt}</span>
            </div>

            <!-- 3-O'RIN (BRONZA) -->
            <div class="podium-card podium-3">
                <div class="avatar-ring">
                    <img src="{p3_img}" alt="{p3_name}" class="avatar-img" onerror="this.src='https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80'">
                </div>
                <span class="place-tag tag-3">🥉 3-O'RIN</span>
                <h3 class="podium-name">{p3_name}</h3>
                <span class="podium-title">{p3_title}</span>
                <span class="podium-amount">{p3_amt}</span>
            </div>
        </section>
        """

    # Table section
    if rows_html:
        html_content += f"""
        <section class="table-section">
            <div class="section-header">
                <h2 class="section-title">
                    <span>🏆</span> Barcha Ishtirokchilar Reytingi
                </h2>
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 Do'stingizni qidiring..." onkeyup="filterTable()">
            </div>

            <table class="leaderboard-table" id="leaderboardTable">
                <thead>
                    <tr>
                        <th style="width: 70px;">O'rin</th>
                        <th>Ism & Unvoni</th>
                        <th style="width: 170px;">Kiritilgan Summa</th>
                        <th style="width: 120px;" class="date-col">Sana</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </section>
        """
    elif empty_state_html:
        html_content += empty_state_html

    html_content += f"""
    </main>

    <footer>
        <p>© 2026 <b>FORBES UZBEKISTAN</b> • Rasmiy Telegram Bot: <a href="https://t.me/{bot_username}" target="_blank">@{bot_username}</a></p>
        <p style="margin-top: 6px; font-size: 0.8rem; color: #64748b;">Har bir to'lov do'stlik va ko'ngilochar maqsadlarda qabul qilinadi.</p>
    </footer>

    <script>
        function filterTable() {{
            const input = document.getElementById("searchInput");
            const filter = input.value.toLowerCase();
            const table = document.getElementById("leaderboardTable");
            if (!table) return;
            const rows = table.getElementsByClassName("table-row");

            for (let i = 0; i < rows.length; i++) {{
                const nameEl = rows[i].querySelector(".user-name");
                const titleEl = rows[i].querySelector(".user-title");
                const text = (nameEl ? nameEl.textContent : "") + " " + (titleEl ? titleEl.textContent : "");
                if (text.toLowerCase().indexOf(filter) > -1) {{
                    rows[i].style.display = "";
                }} else {{
                    rows[i].style.display = "none";
                }}
            }}
        }}

        function shareLeaderboard() {{
            const shareData = {{
                title: "👑 FORBES UZBEKISTAN — Jonli Reyting",
                text: "Kim do'sti uchun eng ko'p pul tashladi? Jonli reytingni ko'ring yoki o'zingiznikini qo'shing!",
                url: window.location.href
            }};
            if (navigator.share) {{
                navigator.share(shareData).catch(() => {{}});
            }} else {{
                const tgUrl = "https://t.me/share/url?url=" + encodeURIComponent(window.location.href) + "&text=" + encodeURIComponent(shareData.text);
                window.open(tgUrl, "_blank");
            }}
        }}
    </script>
</body>
</html>
"""
    return html_content
