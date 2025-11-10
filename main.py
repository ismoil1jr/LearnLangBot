import os
import asyncio
import logging
import sqlite3
from typing import List, Optional
from aiogram.filters import CommandObject

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8259091062:AAGx8cD1P8lMvc7g9xZni7_-C0YbPmt3VMY")
ADMIN_IDS = {5690099705, 7407616559}

DB_FILE = "learnlang.db"
CATS_PER_PAGE = 4
SUBCAT_PER_PAGE = 10
THEME_PER_PAGE = 12
LESSON_PER_PAGE = 12

logging.basicConfig(level=logging.INFO)

# Faqat bot obyektini yaratamiz, sessionni keyinroq
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --------------- DB HELPERS --------------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def update_db_schema():
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("PRAGMA table_info(lessons)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'description' not in columns:
        cur.execute("ALTER TABLE lessons ADD COLUMN description TEXT")
        print("Added description column to lessons table")
    
    if 'image_id' not in columns:
        cur.execute("ALTER TABLE lessons ADD COLUMN image_id TEXT")
        print("Added image_id column to lessons table")
    
    conn.commit()
    conn.close()

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'en'
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subcategory_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY(subcategory_id) REFERENCES subcategories(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT NOT NULL,
            image_id TEXT,
            "order" INTEGER DEFAULT 0,
            FOREIGN KEY(theme_id) REFERENCES themes(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY Key
        );
        """
    )
    for aid in ADMIN_IDS:
        try:
            cur.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (aid,))
        except Exception:
            pass
    conn.commit()
    conn.close()
    update_db_schema()

# ---------- CRUD FUNCTIONS ----------
# Categories
def add_category(title: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (title) VALUES (?)", (title,))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def edit_category(cid: int, new_title: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE categories SET title=? WHERE id=?", (new_title, cid))
    conn.commit()
    conn.close()

def delete_category(cid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE id=?", (cid,))
    conn.commit()
    conn.close()

def list_categories(offset=0, limit=100) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY id LIMIT ? OFFSET ?", (limit, offset))
    rows = cur.fetchall()
    conn.close()
    return rows

def count_categories() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM categories")
    n = cur.fetchone()[0]
    conn.close()
    return n

# Subcategories
def add_subcategory(category_id: int, title: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO subcategories (category_id, title) VALUES (?,?)", (category_id, title))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid

def edit_subcategory(sid: int, new_title: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE subcategories SET title=? WHERE id=?", (new_title, sid))
    conn.commit()
    conn.close()

def delete_subcategory(sid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM subcategories WHERE id=?", (sid,))
    conn.commit()
    conn.close()

def list_subcategories(category_id: int, offset=0, limit=100) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM subcategories WHERE category_id=? ORDER BY id LIMIT ? OFFSET ?",
        (category_id, limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def count_subcategories(category_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM subcategories WHERE category_id=?", (category_id,))
    n = cur.fetchone()[0]
    conn.close()
    return n

# Themes
def add_theme(subcategory_id: int, title: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO themes (subcategory_id, title) VALUES (?,?)", (subcategory_id, title))
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid

def edit_theme(tid: int, new_title: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE themes SET title=? WHERE id=?", (new_title, tid))
    conn.commit()
    conn.close()

def delete_theme(tid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM themes WHERE id=?", (tid,))
    conn.commit()
    conn.close()

def list_themes(subcategory_id: int, offset=0, limit=100) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM themes WHERE subcategory_id=? ORDER BY id LIMIT ? OFFSET ?",
        (subcategory_id, limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def count_themes(subcategory_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM themes WHERE subcategory_id=?", (subcategory_id,))
    n = cur.fetchone()[0]
    conn.close()
    return n

# Lessons
def add_lesson(theme_id: int, title: str, url: str, description: str = None, image_id: str = None, order: int = 0) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO lessons (theme_id, title, description, url, image_id, "order") VALUES (?,?,?,?,?,?)',
        (theme_id, title, description, url, image_id, order),
    )
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return lid

def edit_lesson(lid: int, new_title: str, new_url: str, new_description: str = None, new_image_id: str = None):
    conn = get_conn()
    cur = conn.cursor()
    if new_image_id:
        cur.execute("UPDATE lessons SET title=?, url=?, description=?, image_id=? WHERE id=?", 
                   (new_title, new_url, new_description, new_image_id, lid))
    else:
        cur.execute("UPDATE lessons SET title=?, url=?, description=? WHERE id=?", 
                   (new_title, new_url, new_description, lid))
    conn.commit()
    conn.close()

def delete_lesson(lid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM lessons WHERE id=?", (lid,))
    conn.commit()
    conn.close()

def list_lessons(theme_id: int, offset=0, limit=100) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT * FROM lessons WHERE theme_id=? ORDER BY "order" ASC, id LIMIT ? OFFSET ?',
        (theme_id, limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def count_lessons(theme_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM lessons WHERE theme_id=?", (theme_id,))
    n = cur.fetchone()[0]
    conn.close()
    return n

def get_lesson(lesson_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,))
    row = cur.fetchone()
    conn.close()
    return row

# Users
def add_user_if_not_exists(tg_id: int, lang: str = "en"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, lang) VALUES (?,?)", (tg_id, lang))
    conn.commit()
    conn.close()

def set_user_lang(tg_id: int, lang: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET lang=? WHERE id=?", (lang, tg_id))
    conn.commit()
    conn.close()

def get_user_lang(tg_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT lang FROM users WHERE id=?", (tg_id,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else "en"

def get_all_user_ids() -> List[int]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ---------------- FSM STATES ----------------
class AdminAddCategory(StatesGroup):
    waiting_for_title = State()

class AdminEditCategory(StatesGroup):
    waiting_for_new_title = State()

class AdminAddSubcategory(StatesGroup):
    waiting_for_title = State()

class AdminEditSubcategory(StatesGroup):
    waiting_for_new_title = State()

class AdminAddTheme(StatesGroup):
    waiting_for_title = State()

class AdminEditTheme(StatesGroup):
    waiting_for_new_title = State()

class AdminAddLesson(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_image = State()
    waiting_for_url = State()

class AdminEditLesson(StatesGroup):
    waiting_for_new_title = State()
    waiting_for_new_description = State()
    waiting_for_new_image = State()
    waiting_for_new_url = State()

class AnnounceFlow(StatesGroup):
    waiting_for_photo = State()
    waiting_for_caption = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()

# --------------- UI HELPERS ----------------
def lang_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            ]
        ]
    )

def get_back_button(user_lang: str, callback_data: str):
    text = "⬅️ Orqaga" if user_lang == "uz" else "⬅️ Back"
    return InlineKeyboardButton(text=text, callback_data=callback_data)

def get_main_menu_button(user_lang: str):
    text = "🏠 Bosh menyu" if user_lang == "uz" else "🏠 Main menu"
    return InlineKeyboardButton(text=text, callback_data="main_menu")


def get_navigation_buttons(user_lang: str, page: int, total: int, per_page: int, callback_prefix: str):
    buttons = []
    if page > 0:
        back_text = "⬅️ Orqaga" if user_lang == "uz" else "⬅️ Back"
        buttons.append(InlineKeyboardButton(text=back_text, callback_data=f"{callback_prefix}:{page-1}"))
    if (page + 1) * per_page < total:
        next_text = "Keyingi ➡️" if user_lang == "uz" else "Next ➡️"
        buttons.append(InlineKeyboardButton(text=next_text, callback_data=f"{callback_prefix}:{page+1}"))
    return buttons

# top-level categories pagination
def categories_kb(page: int = 0, is_admin: bool = False, user_lang: str = "uz") -> InlineKeyboardMarkup:
    total = count_categories()
    offset = page * CATS_PER_PAGE
    rows = list_categories(offset=offset, limit=CATS_PER_PAGE)
    
    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(text=r["title"], callback_data=f"cat:{r['id']}")])
    
    nav_buttons = get_navigation_buttons(user_lang, page, total, CATS_PER_PAGE, "cats_page")
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Add admin menu button only for admins
    if is_admin:
        admin_text = "👨‍💻 Admin Menu" if user_lang == "uz" else "👨‍💻 Admin Menu"
        buttons.append([InlineKeyboardButton(text=admin_text, callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def subcategories_kb(category_id: int, page: int = 0, is_admin: bool = False, user_lang: str = "uz") -> InlineKeyboardMarkup:
    total = count_subcategories(category_id)
    offset = page * SUBCAT_PER_PAGE
    rows = list_subcategories(category_id, offset=offset, limit=SUBCAT_PER_PAGE)
    
    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(text=r["title"], callback_data=f"subcat:{r['id']}")])
    
    nav_buttons = get_navigation_buttons(user_lang, page, total, SUBCAT_PER_PAGE, f"subcats:{category_id}")
    if nav_buttons:
        buttons.append(nav_buttons)
    
    back_text = "📂 Kategoriyalarga qaytish" if user_lang == "uz" else "📂 Back to categories"
    buttons.append([get_back_button(user_lang, f"cats_page:0")])
    buttons.append([get_main_menu_button(user_lang)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def themes_kb(subcategory_id: int, page: int = 0, is_admin: bool = False, user_lang: str = "uz") -> InlineKeyboardMarkup:
    total = count_themes(subcategory_id)
    offset = page * THEME_PER_PAGE
    rows = list_themes(subcategory_id, offset=offset, limit=THEME_PER_PAGE)
    
    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(text=r["title"], callback_data=f"theme:{r['id']}")])
    
    nav_buttons = get_navigation_buttons(user_lang, page, total, THEME_PER_PAGE, f"themes:{subcategory_id}")
    if nav_buttons:
        buttons.append(nav_buttons)
    
    parent_cat = get_subcategory_category(subcategory_id)
    back_text = "📁 Subkategoriyalarga qaytish" if user_lang == "uz" else "📁 Back to subcategories"
    buttons.append([get_back_button(user_lang, f"subcats:{parent_cat}:0")])
    buttons.append([get_main_menu_button(user_lang)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lessons_kb(theme_id: int, page: int = 0, is_admin: bool = False, user_lang: str = "uz") -> InlineKeyboardMarkup:
    total = count_lessons(theme_id)
    offset = page * LESSON_PER_PAGE
    rows = list_lessons(theme_id, offset=offset, limit=LESSON_PER_PAGE)
    
    buttons = []
    for idx, r in enumerate(rows, start=offset+1):
        buttons.append([InlineKeyboardButton(text=f"{idx}. {r['title']}", callback_data=f"lesson:{r['id']}")])
    
    nav_buttons = get_navigation_buttons(user_lang, page, total, LESSON_PER_PAGE, f"lessons:{theme_id}")
    if nav_buttons:
        buttons.append(nav_buttons)
    
    parent_subcat = get_theme_subcategory(theme_id)
    back_text = "📝 Mavzularga qaytish" if user_lang == "uz" else "📝 Back to themes"
    buttons.append([get_back_button(user_lang, f"themes:{parent_subcat}:0")])
    buttons.append([get_main_menu_button(user_lang)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_menu_kb(user_lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="admin_add_cat")],
        [InlineKeyboardButton(text="📋 Kategoriyalar ro'yxati", callback_data="admin_list_cats")],
        [InlineKeyboardButton(text="📢 E'lon qilish", callback_data="admin_anons")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ---------- Utility getters ----------
def get_subcategory_category(subcategory_id: int) -> Optional[int]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT category_id FROM subcategories WHERE id=?", (subcategory_id,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None

def get_theme_subcategory(theme_id: int) -> Optional[int]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT subcategory_id FROM themes WHERE id=?", (theme_id,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None


# ---------------- HANDLERS ----------------
@dp.message(Command("start"))
async def cmd_start(m: Message):
    user_id = m.from_user.id
    add_user_if_not_exists(user_id)
    user_lang = get_user_lang(user_id)
    
    # Agar foydalanuvchi til tanlamagan bo'lsa
    if user_lang == "en":
        await m.answer("Assalomu alaykum! Iltimos, tilni tanlang:\n\nHello! Please choose your language:", reply_markup=lang_kb())
    else:
        is_admin_user = is_admin(user_id)
        welcome_text = "Assalomu alaykum! Kategoriyani tanlang:" if user_lang == "uz" else "Welcome! Choose a category:"
        await m.answer(welcome_text, reply_markup=categories_kb(page=0, is_admin=is_admin_user, user_lang=user_lang))

@dp.message(Command("help"))
async def cmd_help(m: Message):
    user_lang = get_user_lang(m.from_user.id)
    
    if user_lang == "uz":
        help_text = """🤖 <b>Botdan foydalanish bo'yicha ko'rsatma:</b>

/start - Botni ishga tushirish
/help - Yordam olish
/lang - Tilni o'zgartirish
/admin - Admin paneliga kirish (faqat adminlar uchun)

📚 <b>Bot funksiyalari:</b>
• Kategoriyalar bo'yicha darslarni ko'rish
• Video darslarni tomosha qilish
• Tilni o'zbek yoki ingliz tiliga o'zgartirish

🎓 <b>Qanday foydalanish:</b>
1. Kategoriyani tanlang
2. Subkategoriyani tanlang  
3. Mavzuni tanlang
4. Darsni tanlang va tomosha qiling"""
    else:
        help_text = """🤖 <b>Bot usage guide:</b>

/start - Start the bot
/help - Get help
/lang - Change language  
/admin - Access admin panel (admins only)

📚 <b>Bot features:</b>
• View lessons by categories
• Watch video lessons
• Change language to Uzbek or English

🎓 <b>How to use:</b>
1. Choose a category
2. Choose a subcategory
3. Choose a theme
4. Select a lesson and watch"""
    
    await m.answer(help_text, parse_mode="HTML")

@dp.message(Command("lang"))
async def cmd_lang(m: Message):
    user_lang = get_user_lang(m.from_user.id)
    text = "Tilni tanlang / Choose language:" if user_lang == "uz" else "Choose language:"
    await m.answer(text, reply_markup=lang_kb())

@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(c: CallbackQuery):
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    welcome_text = "Bosh menyu. Kategoriyani tanlang:" if user_lang == "uz" else "Main menu. Choose a category:"
    
    # Agar xabar tahrirlab bo'lmasa, yangi xabar yuboramiz
    try:
        await c.message.edit_text(welcome_text, reply_markup=categories_kb(page=0, is_admin=is_admin_user, user_lang=user_lang))
    except:
        await c.message.answer(welcome_text, reply_markup=categories_kb(page=0, is_admin=is_admin_user, user_lang=user_lang))
    
    await c.answer()

@dp.callback_query(F.data.in_(["lang_uz", "lang_en"]))
async def set_language(c: CallbackQuery):
    lang = "uz" if c.data == "lang_uz" else "en"
    set_user_lang(c.from_user.id, lang)
    
    is_admin_user = is_admin(c.from_user.id)
    
    if lang == "uz":
        try:
            await c.message.edit_text("Til o'zbekcha ga o'zgartirildi ✅")
        except:
            pass
        await c.message.answer("Assalomu alaykum! Kategoriyani tanlang:", 
                             reply_markup=categories_kb(page=0, is_admin=is_admin_user, user_lang=lang))
    else:
        try:
            await c.message.edit_text("Language changed to English ✅")
        except:
            pass
        await c.message.answer("Welcome! Choose a category:", 
                             reply_markup=categories_kb(page=0, is_admin=is_admin_user, user_lang=lang))
    await c.answer()

# Categories pagination
@dp.callback_query(F.data.startswith("cats_page:"))
async def cats_page_cb(c: CallbackQuery):
    page = int(c.data.split(":", 1)[1])
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    text = "Kategoriyalar:" if user_lang == "uz" else "Categories:"
    await c.message.edit_text(text, reply_markup=categories_kb(page=page, is_admin=is_admin_user, user_lang=user_lang))
    await c.answer()

# Open a category => show subcategories
@dp.callback_query(F.data.startswith("cat:"))
async def open_category(c: CallbackQuery):
    cat_id = int(c.data.split(":", 1)[1])
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    text = "Subkategoriyalar:" if user_lang == "uz" else "Subcategories:"
    await c.message.edit_text(text, reply_markup=subcategories_kb(cat_id, page=0, is_admin=is_admin_user, user_lang=user_lang))
    await c.answer()

# Subcategories pagination
@dp.callback_query(F.data.startswith("subcats:"))
async def subcats_page_cb(c: CallbackQuery):
    parts = c.data.split(":")
    category_id = int(parts[1])
    page = int(parts[2])
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    text = "Subkategoriyalar:" if user_lang == "uz" else "Subcategories:"
    await c.message.edit_text(text, reply_markup=subcategories_kb(category_id, page=page, is_admin=is_admin_user, user_lang=user_lang))
    await c.answer()

# Open subcategory => show themes
@dp.callback_query(F.data.startswith("subcat:"))
async def open_subcategory(c: CallbackQuery):
    sid = int(c.data.split(":", 1)[1])
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    text = "Mavzular:" if user_lang == "uz" else "Themes:"
    await c.message.edit_text(text, reply_markup=themes_kb(sid, page=0, is_admin=is_admin_user, user_lang=user_lang))
    await c.answer()

# Themes pagination
@dp.callback_query(F.data.startswith("themes:"))
async def themes_page_cb(c: CallbackQuery):
    parts = c.data.split(":")
    subcat_id = int(parts[1])
    page = int(parts[2])
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    text = "Mavzular:" if user_lang == "uz" else "Themes:"
    await c.message.edit_text(text, reply_markup=themes_kb(subcat_id, page=page, is_admin=is_admin_user, user_lang=user_lang))
    await c.answer()

# Open theme => show lessons
@dp.callback_query(F.data.startswith("theme:"))
async def open_theme(c: CallbackQuery):
    tid = int(c.data.split(":", 1)[1])
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    text = "Darslar:" if user_lang == "uz" else "Lessons:"
    await c.message.edit_text(text, reply_markup=lessons_kb(tid, page=0, is_admin=is_admin_user, user_lang=user_lang))
    await c.answer()

# Lessons pagination
# Lessons pagination
@dp.callback_query(F.data.startswith("lessons:"))
async def lessons_page_cb(c: CallbackQuery):
    parts = c.data.split(":")
    theme_id = int(parts[1])
    page = int(parts[2])
    user_lang = get_user_lang(c.from_user.id)
    is_admin_user = is_admin(c.from_user.id)
    
    text = "Darslar:" if user_lang == "uz" else "Lessons:"
    
    try:
        await c.message.edit_text(text, reply_markup=lessons_kb(theme_id, page=page, is_admin=is_admin_user, user_lang=user_lang))
    except:
        # Agar xabarni tahrirlab bo'lmasa, yangi xabar yuboramiz
        await c.message.answer(text, reply_markup=lessons_kb(theme_id, page=page, is_admin=is_admin_user, user_lang=user_lang))
        await c.message.delete()  # Eski xabarni o'chiramiz
    
    await c.answer()

# Open lesson -> show lesson details with image and description
# Open lesson -> show lesson details with image and description
# Open lesson -> show lesson details with image and description
@dp.callback_query(F.data.startswith("lesson:"))
async def open_lesson(c: CallbackQuery):
    lid = int(c.data.split(":", 1)[1])
    lesson = get_lesson(lid)
    user_lang = get_user_lang(c.from_user.id)
    
    if not lesson:
        alert_text = "Dars topilmadi" if user_lang == "uz" else "Lesson not found"
        await c.answer(alert_text, show_alert=True)
        return
    
    button_text = "📖 Darsni ko'rish" if user_lang == "uz" else "📖 Open lesson"
    
    # Theme ID ni olamiz
    theme_id = lesson["theme_id"]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, url=lesson["url"])],
        [get_back_button(user_lang, f"lessons:{theme_id}:0"), get_main_menu_button(user_lang)]
    ])
    
    caption = f"🎯 {lesson['title']}\n\n{lesson['description'] or ''}"
    
    try:
        if lesson["image_id"]:
            # Agar rasmli xabar bo'lsa, eski xabarni o'chirib yangisini yuboramiz
            await c.message.delete()
            await c.message.answer_photo(photo=lesson["image_id"], caption=caption, reply_markup=kb)
        else:
            # Agar faqat matn bo'lsa, xabarni tahrirlaymiz
            await c.message.edit_text(caption, reply_markup=kb)
    except Exception as e:
        # Agar xatolik yuzaga kelsa, yangi xabar yuboramiz
        if lesson["image_id"]:
            await c.message.answer_photo(photo=lesson["image_id"], caption=caption, reply_markup=kb)
        else:
            await c.message.answer(caption, reply_markup=kb)
    
    await c.answer()

# ----------------- ADMIN ------------------
@dp.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        user_lang = get_user_lang(m.from_user.id)
        text = "Sizda admin huquqi yo'q." if user_lang == "uz" else "You don't have admin rights."
        await m.answer(text)
        return
    
    user_lang = get_user_lang(m.from_user.id)
    text = "Admin menyusi:" if user_lang == "uz" else "Admin menu:"
    await m.answer(text, reply_markup=admin_menu_kb(user_lang))

@dp.callback_query(F.data == "admin_menu")
async def admin_menu_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        user_lang = get_user_lang(c.from_user.id)
        alert_text = "Siz admin emassiz" if user_lang == "uz" else "You are not admin"
        await c.answer(alert_text, show_alert=True)
        return
    
    user_lang = get_user_lang(c.from_user.id)
    text = "Admin menyusi:" if user_lang == "uz" else "Admin menu:"
    
    try:
        await c.message.edit_text(text, reply_markup=admin_menu_kb(user_lang))
    except:
        await c.message.answer(text, reply_markup=admin_menu_kb(user_lang))
    
    await c.answer()

# Add category
@dp.callback_query(F.data == "admin_add_cat")
async def admin_add_cat_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    await c.message.answer("Yangi kategoriya nomini kiriting:")
    await state.set_state(AdminAddCategory.waiting_for_title)
    await c.answer()

@dp.message(AdminAddCategory.waiting_for_title)
async def admin_receive_cat_title(m: Message, state: FSMContext):
    title = m.text.strip()
    cid = add_category(title)
    
    # Store the category ID for the next step
    await state.update_data(new_category_id=cid)
    
    # Ask if admin wants to add a subcategory now
    buttons = [
        [InlineKeyboardButton(text="✅ Ha, subkategoriya qo'shish", callback_data=f"admin_add_subcat_now:{cid}")],
        [InlineKeyboardButton(text="❌ Yo'q, keyinroq", callback_data="admin_menu")]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await m.answer(f"Kategoriya qo'shildi: {title} (id={cid}).\nHozir subkategoriya qo'shmoqchimisiz?", reply_markup=kb)
    await state.clear()

# Handler for adding subcategory immediately after category
@dp.callback_query(F.data.startswith("admin_add_subcat_now:"))
async def admin_add_subcat_now_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    
    cid = int(c.data.split(":", 1)[1])
    await c.message.answer("Subkategoriya nomini kiriting (/empty bo'sh qoldirish uchun):")
    await state.update_data(target_category=cid)
    await state.set_state(AdminAddSubcategory.waiting_for_title)
    await c.answer()

# List categories (admin) -> choose category to edit/delete/add subcat
@dp.callback_query(F.data == "admin_list_cats")
async def admin_list_cats_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    cats = list_categories(0, 1000)
    buttons = []
    for cat in cats:
        buttons.append([InlineKeyboardButton(text=cat["title"], callback_data=f"admin_cat:{cat['id']}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text("Barcha kategoriyalar:", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("admin_cat:"))
async def admin_cat_detail_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    cid = int(c.data.split(":", 1)[1])
    
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_cat_edit:{cid}"),
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin_cat_del:{cid}")
        ],
        [
            InlineKeyboardButton(text="➕ Subkategoriya qo'shish", callback_data=f"admin_add_subcat_choose:{cid}"),
            InlineKeyboardButton(text="📋 Subkategoriyalar", callback_data=f"admin_list_subcats:{cid}")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_list_cats")]
    ]
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text(f"Kategoriya ID={cid}", reply_markup=kb)
    await c.answer()

# Edit category
@dp.callback_query(F.data.startswith("admin_cat_edit:"))
async def admin_cat_edit_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    cid = int(c.data.split(":", 1)[1])
    await c.message.answer("Yangi kategoriya nomini kiriting:")
    await state.update_data(edit_cat_id=cid)
    await state.set_state(AdminEditCategory.waiting_for_new_title)
    await c.answer()

@dp.message(AdminEditCategory.waiting_for_new_title)
async def admin_cat_do_edit(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = data.get("edit_cat_id")
    if not cid:
        await m.answer("Kategoriya topilmadi."); await state.clear(); return
    new_title = m.text.strip()
    edit_category(cid, new_title)
    await m.answer(f"Kategoriya yangilandi: {new_title}")
    await state.clear()

# Delete category
@dp.callback_query(F.data.startswith("admin_cat_del:"))
async def admin_cat_del_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    cid = int(c.data.split(":", 1)[1])
    delete_category(cid)
    await c.message.edit_text("Kategoriya o'chirildi.", reply_markup=admin_menu_kb())
    await c.answer()

# ---------------- Subcategory admin ----------------
@dp.callback_query(F.data.startswith("admin_add_subcat_choose:"))
async def admin_add_subcat_choose_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    cid = int(c.data.split(":", 1)[1])
    await c.message.answer("Subkategoriya nomini kiriting (/empty bo'sh qoldirish uchun):")
    await state.update_data(target_category=cid)
    await state.set_state(AdminAddSubcategory.waiting_for_title)
    await c.answer()

@dp.message(AdminAddSubcategory.waiting_for_title)
async def admin_receive_subcat_title(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = data.get("target_category")
    title = m.text.strip()
    
    if title.lower() == "/empty":
        sid = add_subcategory(cid, " ")
        await m.answer(f"Bo'sh subkategoriya qo'shildi (id={sid}).")
    else:
        sid = add_subcategory(cid, title)
        await m.answer(f"Subkategoriya qo'shildi: {title} (id={sid})")
    
    # Ask if admin wants to add a theme now
    buttons = [
        [InlineKeyboardButton(text="✅ Ha, mavzu qo'shish", callback_data=f"admin_add_theme_now:{sid}")],
        [InlineKeyboardButton(text="❌ Yo'q, keyinroq", callback_data="admin_menu")]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await m.answer("Hozir mavzu qo'shmoqchimisiz?", reply_markup=kb)
    await state.clear()

# Handler for adding theme immediately after subcategory
@dp.callback_query(F.data.startswith("admin_add_theme_now:"))
async def admin_add_theme_now_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    
    sid = int(c.data.split(":", 1)[1])
    await c.message.answer("Mavzu nomini kiriting (/empty bo'sh qoldirish uchun):")
    await state.update_data(target_subcategory=sid)
    await state.set_state(AdminAddTheme.waiting_for_title)
    await c.answer()

@dp.callback_query(F.data.startswith("admin_list_subcats:"))
async def admin_list_subcats_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    cid = int(c.data.split(":", 1)[1])
    subs = list_subcategories(cid, 0, 1000)
    buttons = []
    for s in subs:
        buttons.append([InlineKeyboardButton(text=s["title"], callback_data=f"admin_subcat:{s['id']}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_list_cats")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text("Subkategoriyalar:", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("admin_subcat:"))
async def admin_subcat_detail_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    sid = int(c.data.split(":", 1)[1])
    
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_subcat_edit:{sid}"),
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin_subcat_del:{sid}")
        ],
        [
            InlineKeyboardButton(text="➕ Mavzu qo'shish", callback_data=f"admin_add_theme_choose:{sid}"),
            InlineKeyboardButton(text="📋 Mavzular", callback_data=f"admin_list_themes:{sid}")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_list_cats")]
    ]
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text(f"Subkategoriya ID={sid}", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("admin_subcat_edit:"))
async def admin_subcat_edit_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    sid = int(c.data.split(":", 1)[1])
    await c.message.answer("Yangi subkategoriya nomini kiriting:")
    await state.update_data(edit_subcat_id=sid)
    await state.set_state(AdminEditSubcategory.waiting_for_new_title)
    await c.answer()

@dp.message(AdminEditSubcategory.waiting_for_new_title)
async def admin_subcat_do_edit(m: Message, state: FSMContext):
    data = await state.get_data()
    sid = data.get("edit_subcat_id")
    if not sid:
        await m.answer("Subkategoriya topilmadi."); await state.clear(); return
    new_title = m.text.strip()
    edit_subcategory(sid, new_title)
    await m.answer(f"Subkategoriya yangilandi: {new_title}")
    await state.clear()

@dp.callback_query(F.data.startswith("admin_subcat_del:"))
async def admin_subcat_del_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    sid = int(c.data.split(":", 1)[1])
    delete_subcategory(sid)
    await c.message.edit_text("Subkategoriya o'chirildi.", reply_markup=admin_menu_kb())
    await c.answer()

# ---------------- Theme admin ----------------
@dp.callback_query(F.data.startswith("admin_add_theme_choose:"))
async def admin_add_theme_choose_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    sid = int(c.data.split(":", 1)[1])
    await c.message.answer("Mavzu nomini kiriting (/empty bo'sh qoldirish uchun):")
    await state.update_data(target_subcategory=sid)
    await state.set_state(AdminAddTheme.waiting_for_title)
    await c.answer()

@dp.message(AdminAddTheme.waiting_for_title)
async def admin_receive_theme_title(m: Message, state: FSMContext):
    data = await state.get_data()
    sid = data.get("target_subcategory")
    title = m.text.strip()
    
    if title.lower() == "/empty":
        tid = add_theme(sid, " ")
        await m.answer(f"Bo'sh mavzu qo'shildi (id={tid}).")
    else:
        tid = add_theme(sid, title)
        await m.answer(f"Mavzu qo'shildi: {title} (id={tid})")
    
    # Ask if admin wants to add a lesson now
    buttons = [
        [InlineKeyboardButton(text="✅ Ha, dars qo'shish", callback_data=f"admin_add_lesson_now:{tid}")],
        [InlineKeyboardButton(text="❌ Yo'q, keyinroq", callback_data="admin_menu")]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await m.answer("Hozir dars qo'shmoqchimisiz?", reply_markup=kb)
    await state.clear()

# Handler for adding lesson immediately after theme
@dp.callback_query(F.data.startswith("admin_add_lesson_now:"))
async def admin_add_lesson_now_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    
    tid = int(c.data.split(":", 1)[1])
    await c.message.answer("Dars nomini kiriting:")
    await state.update_data(target_theme=tid)
    await state.set_state(AdminAddLesson.waiting_for_title)
    await c.answer()

@dp.callback_query(F.data.startswith("admin_list_themes:"))
async def admin_list_themes_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    sid = int(c.data.split(":", 1)[1])
    themes = list_themes(sid, 0, 1000)
    buttons = []
    for t in themes:
        buttons.append([InlineKeyboardButton(text=t["title"], callback_data=f"admin_theme:{t['id']}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_list_cats")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text("Mavzular:", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("admin_theme:"))
async def admin_theme_detail_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    tid = int(c.data.split(":", 1)[1])
    
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_theme_edit:{tid}"),
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin_theme_del:{tid}")
        ],
        [
            InlineKeyboardButton(text="➕ Dars qo'shish", callback_data=f"admin_add_lesson_choose:{tid}"),
            InlineKeyboardButton(text="📋 Darslar", callback_data=f"admin_list_lessons:{tid}")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_list_cats")]
    ]
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text(f"Mavzu ID={tid}", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("admin_theme_edit:"))
async def admin_theme_edit_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    tid = int(c.data.split(":", 1)[1])
    await c.message.answer("Yangi mavzu nomini kiriting:")
    await state.update_data(edit_theme_id=tid)
    await state.set_state(AdminEditTheme.waiting_for_new_title)
    await c.answer()

@dp.message(AdminEditTheme.waiting_for_new_title)
async def admin_theme_do_edit(m: Message, state: FSMContext):
    data = await state.get_data()
    tid = data.get("edit_theme_id")
    if not tid:
        await m.answer("Mavzu topilmadi."); await state.clear(); return
    new_title = m.text.strip()
    edit_theme(tid, new_title)
    await m.answer(f"Mavzu yangilandi: {new_title}")
    await state.clear()

@dp.callback_query(F.data.startswith("admin_theme_del:"))
async def admin_theme_del_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    tid = int(c.data.split(":", 1)[1])
    delete_theme(tid)
    await c.message.edit_text("Mavzu o'chirildi.", reply_markup=admin_menu_kb())
    await c.answer()


# ---------------- Lesson admin ----------------
@dp.callback_query(F.data.startswith("admin_add_lesson_choose:"))
async def admin_add_lesson_choose_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    tid = int(c.data.split(":", 1)[1])
    await c.message.answer("Dars nomini kiriting:")
    await state.update_data(target_theme=tid)
    await state.set_state(AdminAddLesson.waiting_for_title)
    await c.answer()


@dp.message(AdminAddLesson.waiting_for_title)
async def admin_receive_lesson_title(m: Message, state: FSMContext):
    data = await state.get_data()
    tid = data.get("target_theme")
    title = m.text.strip()
    await state.update_data(pending_lesson_title=title)
    await state.set_state(AdminAddLesson.waiting_for_description)
    await m.answer("Endi dars haqida qisqacha ma'lumot kiriting:")

@dp.message(AdminAddLesson.waiting_for_description)
async def admin_receive_lesson_description(m: Message, state: FSMContext):
    description = m.text.strip()
    await state.update_data(pending_lesson_description=description)
    await state.set_state(AdminAddLesson.waiting_for_image)
    await m.answer("Endi dars uchun rasm yuboring (yoki /skip bu qadamni o'tkazib yuborish uchun):")

@dp.message(AdminAddLesson.waiting_for_image, F.photo)
async def admin_receive_lesson_image(m: Message, state: FSMContext):
    file_id = m.photo[-1].file_id
    await state.update_data(pending_lesson_image=file_id)
    await state.set_state(AdminAddLesson.waiting_for_url)
    await m.answer("Endi dars URL manzilini kiriting (https://...):")

@dp.message(AdminAddLesson.waiting_for_image, F.text == "/skip")
async def admin_skip_lesson_image(m: Message, state: FSMContext):
    await state.update_data(pending_lesson_image=None)
    await state.set_state(AdminAddLesson.waiting_for_url)
    await m.answer("Endi dars URL manzilini kiriting (https://...):")

@dp.message(AdminAddLesson.waiting_for_url)
async def admin_receive_lesson_url(m: Message, state: FSMContext):
    data = await state.get_data()
    tid = data.get("target_theme")
    title = data.get("pending_lesson_title")
    description = data.get("pending_lesson_description")
    image_id = data.get("pending_lesson_image")
    url = m.text.strip()
    
    # Automatically determine the order (next number)
    lesson_count = count_lessons(tid)
    order = lesson_count + 1
    
    lid = add_lesson(tid, title, url, description, image_id, order=order)
    await m.answer(f"Dars qo'shildi: {order}. {title} (id={lid})")
    await state.clear()

@dp.callback_query(F.data.startswith("admin_list_lessons:"))
async def admin_list_lessons_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    tid = int(c.data.split(":", 1)[1])
    lessons = list_lessons(tid, 0, 1000)
    buttons = []
    for l in lessons:
        buttons.append([InlineKeyboardButton(text=f"{l['order']}. {l['title']}", callback_data=f"admin_lesson:{l['id']}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_list_cats")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text("Darslar:", reply_markup=kb)
    await c.answer()


# Lesson detail (edit / delete)
@dp.callback_query(F.data.startswith("admin_lesson:"))
async def admin_lesson_detail_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    lid = int(c.data.split(":", 1)[1])
    
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_lesson_edit:{lid}"),
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin_lesson_del:{lid}")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_list_cats")]
    ]
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await c.message.edit_text(f"Dars ID={lid}", reply_markup=kb)
    await c.answer()

# Edit lesson
@dp.callback_query(F.data.startswith("admin_lesson_edit:"))
async def admin_lesson_edit_cb(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    lid = int(c.data.split(":", 1)[1])
    await c.message.answer("Yangi dars nomini kiriting:")
    await state.update_data(edit_lesson_id=lid)
    await state.set_state(AdminEditLesson.waiting_for_new_title)
    await c.answer()

@dp.message(AdminEditLesson.waiting_for_new_title)
async def admin_lesson_edit_title(m: Message, state: FSMContext):
    data = await state.get_data()
    lid = data.get("edit_lesson_id")
    if not lid:
        await m.answer("Dars topilmadi."); await state.clear(); return
    new_title = m.text.strip()
    await state.update_data(new_lesson_title=new_title)
    await state.set_state(AdminEditLesson.waiting_for_new_description)
    await m.answer("Endi yangi dars tavsifini kiriting:")

@dp.message(AdminEditLesson.waiting_for_new_description)
async def admin_lesson_edit_description(m: Message, state: FSMContext):
    new_description = m.text.strip()
    await state.update_data(new_lesson_description=new_description)
    await state.set_state(AdminEditLesson.waiting_for_new_image)
    await m.answer("Endi yangi rasm yuboring (yoki /skip bu qadamni o'tkazib yuborish uchun):")

@dp.message(AdminEditLesson.waiting_for_new_image, F.photo)
async def admin_lesson_edit_image(m: Message, state: FSMContext):
    file_id = m.photo[-1].file_id
    await state.update_data(new_lesson_image=file_id)
    await state.set_state(AdminEditLesson.waiting_for_new_url)
    await m.answer("Endi yangi URL manzilini kiriting:")

@dp.message(AdminEditLesson.waiting_for_new_image, F.text == "/skip")
async def admin_lesson_skip_image(m: Message, state: FSMContext):
    await state.update_data(new_lesson_image=None)
    await state.set_state(AdminEditLesson.waiting_for_new_url)
    await m.answer("Endi yangi URL manzilini kiriting:")

@dp.message(AdminEditLesson.waiting_for_new_url)
async def admin_lesson_edit_url(m: Message, state: FSMContext):
    data = await state.get_data()
    lid = data.get("edit_lesson_id")
    new_title = data.get("new_lesson_title")
    new_description = data.get("new_lesson_description")
    new_image_id = data.get("new_lesson_image")
    new_url = m.text.strip()
    
    edit_lesson(lid, new_title, new_url, new_description, new_image_id)
    await m.answer(f"Dars yangilandi: {new_title}")
    await state.clear()


# Delete lesson
@dp.callback_query(F.data.startswith("admin_lesson_del:"))
async def admin_lesson_del_cb(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Ruxsat yo'q", show_alert=True); return
    lid = int(c.data.split(":", 1)[1])
    delete_lesson(lid)
    await c.message.edit_text("Dars o'chirildi.", reply_markup=admin_menu_kb())
    await c.answer()

# ----------------- Announcements (/anons) ----------------
@dp.callback_query(F.data == "admin_anons")
@dp.message(Command("anons"))
async def admin_anons_entry(event, state: FSMContext):
    # event can be CallbackQuery or Message; unify
    user_id = event.from_user.id
    if not is_admin(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Ruxsat yo'q", show_alert=True)
        else:
            await event.answer("Ruxsat yo'q")
        return
    
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer("E'lon uchun rasm yuboring (yoki /skip faqat matnli e'lon uchun):")
        await state.set_state(AnnounceFlow.waiting_for_photo)
    else:
        # message
        await event.answer("E'lon uchun rasm yuboring (yoki /skip faqat matnli e'lon uchun):")
        await state.set_state(AnnounceFlow.waiting_for_photo)

@dp.message(AnnounceFlow.waiting_for_photo, F.photo)
async def admin_receive_photo(m: Message, state: FSMContext):
    file_id = m.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await m.answer("Endi e'lon matnini kiriting:")
    await state.set_state(AnnounceFlow.waiting_for_caption)

@dp.message(AnnounceFlow.waiting_for_photo, F.text == "/skip")
async def admin_skip_photo(m: Message, state: FSMContext):
    await state.update_data(photo_file_id=None)
    await m.answer("Endi e'lon matnini kiriting:")
    await state.set_state(AnnounceFlow.waiting_for_caption)

@dp.message(AnnounceFlow.waiting_for_caption)
async def admin_receive_caption(m: Message, state: FSMContext):
    caption = m.text
    await state.update_data(caption=caption)
    await m.answer("Endi inline tugma matnini kiriting (yoki /skip tugmasiz e'lon uchun):")
    await state.set_state(AnnounceFlow.waiting_for_button_text)

@dp.message(AnnounceFlow.waiting_for_button_text, F.text == "/skip")
async def admin_skip_button(m: Message, state: FSMContext):
    data = await state.get_data()
    caption = data.get("caption")
    photo_id = data.get("photo_file_id")
    
    user_ids = get_all_user_ids()
    sent = 0
    failed = 0
    
    for uid in user_ids:
        try:
            if photo_id:
                await bot.send_photo(uid, photo=photo_id, caption=caption)
            else:
                await bot.send_message(uid, caption)
            sent += 1
        except Exception:
            failed += 1
    
    await m.answer(f"E'lon {sent} foydalanuvchiga yuborildi, {failed} foydalanuvchiga yuborib bo'lmadi.")
    await state.clear()

@dp.message(AnnounceFlow.waiting_for_button_text)
async def admin_receive_button_text(m: Message, state: FSMContext):
    button_text = m.text
    await state.update_data(button_text=button_text)
    await m.answer("Endi inline tugma URL manzilini kiriting:")
    await state.set_state(AnnounceFlow.waiting_for_button_url)

@dp.message(AnnounceFlow.waiting_for_button_url)
async def admin_receive_button_url(m: Message, state: FSMContext):
    data = await state.get_data()
    caption = data.get("caption")
    photo_id = data.get("photo_file_id")
    button_text = data.get("button_text")
    button_url = m.text
    
    # Create inline keyboard with the button
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, url=button_url)]
    ])
    
    user_ids = get_all_user_ids()
    sent = 0
    failed = 0
    
    for uid in user_ids:
        try:
            if photo_id:
                await bot.send_photo(uid, photo=photo_id, caption=caption, reply_markup=kb)
            else:
                await bot.send_message(uid, caption, reply_markup=kb)
            sent += 1
        except Exception:
            failed += 1
    
    await m.answer(f"E'lon {sent} foydalanuvchiga yuborildi, {failed} foydalanuvchiga yuborib bo'lmadi.")
    await state.clear()


# Close button
@dp.callback_query(F.data == "close")
async def close_cb(c: CallbackQuery):
    try:
        await c.message.delete()
    except Exception:
        pass
    await c.answer()

# fallback (silently answer unknown)
@dp.callback_query()
async def fallback_cb(c: CallbackQuery):
    await c.answer()

# ---------------- STARTUP ----------------
async def main():
    init_db()
    update_db_schema()  # <-- Bu qatorni qo'shing
    logging.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())