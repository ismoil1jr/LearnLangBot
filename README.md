LearnLangBot — Project Overview and How It Works

Project purpose
LearnLangBot is a Telegram bot that provides free lessons to users. Lessons are organized into categories (for example: Languages, Backend, Frontend, Speaking, Writing). Each category contains subcategories (for example: Backend → Python, PHP, Go), each subcategory contains topics (for example: Python → def, class, loops), and each topic contains one or more lessons. A lesson is a small record with teacher name and a lesson URL (YouTube or your own site). Admins can add, edit and delete categories, subcategories, topics, and lessons through a chat-driven admin flow inside the bot.

Tech stack (what this project uses)

Programming language: Python

Bot framework: aiogram (recommended, async and simple)

Database: SQLite3 (lightweight and fine for MVP). Use ORM or plain sqlite3 as you prefer. Later you can migrate to PostgreSQL when scaling.

Deployment: Start by running on your machine or a small VPS; when needed, migrate database and run worker/process manager.

Files you will have (simple list)

main.py — bot entry file, contains handlers, command flow, and admin checks.

database.py — small helper that initializes the SQLite database and provides CRUD helper functions.

README.txt — this descriptive file (what you are copying now).

learnlangbot.db — the SQLite database file created at runtime.

Simple data design (human-readable, one-line per table)

categories: id, name

subcategories: id, category_id, name

topics: id, subcategory_id, name

lessons: id, topic_id, teacher_name, video_url

User flow (step-by-step, linear)

User sends /start.

Bot greets and asks the user to choose language (English or Uzbek).

After language selection, bot explains how to use the bot and lists available commands.

User asks to see categories (for example via /categories or a keyboard button).

Bot shows categories as buttons (inline or reply keyboard).

User selects a category → bot shows subcategories for that category.

User selects a subcategory → bot shows topics for that subcategory.

User selects a topic → bot lists lessons for that topic. Each lesson shows teacher name and lesson URL.

User opens the lesson URL to learn (YouTube or your site).

Admin flow (how an admin adds content via chat)

Admin runs /admin (or a secret command). Admin is validated by Telegram user id (ADMIN_ID).

Bot shows admin actions: add category, add subcategory, add topic, add lesson, edit, delete.

Admin chooses "add category" → bot asks "Type category name" → admin types it → bot confirms and saves.

Admin chooses "add subcategory" → bot asks which category (show buttons) → admin selects category → bot asks subcategory name → admin types → bot saves.

Admin chooses "add topic" → bot asks which subcategory (buttons) → admin selects → bot asks topic name → admin types → bot saves.

Admin chooses "add lesson" → bot asks which topic → admin selects → bot asks teacher name → admin types → bot asks video URL → admin types → bot saves.

Edit/delete follow a similar selection and confirmation flow. Admin should always confirm destructive actions (delete → confirm yes/no).

Commands the bot should support (basic set)

/start — start and choose language

/help — show quick help and available commands

/categories — list categories

/admin — enter admin panel (admin only)

/add_category — quick shortcut for admin

/add_subcategory — admin shortcut

/add_topic — admin shortcut

/add_lesson — admin shortcut

(optional) /search — search topics or lessons by keyword

Implementation notes and small rules

Use finite-state machine (FSM) for admin multi-step flows (so the bot "remembers" the current step: choosing parent, entering name, entering URL).

Protect admin actions by checking sender's Telegram ID against ADMIN_ID.

Use reply keyboards for top-level lists (categories, subcategories) and inline keyboards for actions (edit / delete / confirm).

Keep database calls simple and synchronous if you use sqlite3 module, or use an async wrapper if you want full async. For MVP, simple sqlite3 with transactions is fine.

Always validate URLs for lessons (basic check that it starts with http or https).

On delete actions, ask for explicit confirmation before deleting a record.

Keep user-facing text localized (two language files or small dict) so English and Uzbek can be shown based on user's language selection.

How the admin chat-driven creation should behave (principles)

Step-by-step prompts: bot asks exactly one question at a time and waits for reply.

When choosing where to add (for example, adding a topic), present existing parents as buttons so admin cannot type an invalid name.

After every successful create/edit/delete, bot sends a concise confirmation message.

Allow admin to cancel any operation with a "Cancel" button or by sending /cancel.

How to run locally (short instructions)

Install Python 3.10+.

Install required package: aiogram (pip install aiogram).

Put your Telegram bot token into the code (secure it — do not push token to public repos).

Put your Telegram numeric ID into the code as ADMIN_ID.

Run the bot (python main.py). The bot will create the SQLite database file on first run.

Talk to the bot from a Telegram account. Admin commands work for the account with ADMIN_ID.

Scaling notes and future-proofing

When user count grows and you move to a server, switch from SQLite to PostgreSQL. Use a lightweight ORM or write database access functions so swapping DB backends is minimal work.

Consider adding a tiny web admin panel later if chat CRUD becomes cumbersome.

If you plan to attach AI features later (automatic lesson suggestions, auto-categorization), keep lesson records structured and include metadata (duration, tags) so models can use them.

Add pagination if lists get long. Use inline keyboards with "Next" and "Prev".

Track analytics (which lessons are clicked) if you want to measure what users like.

Security and safety

Never log full admin tokens or put them in public code.

Validate and sanitize user input where applicable.

Limit possible actions to admin IDs only for create/update/delete.

Minimal UX tips for the frontend-minded partner

Use short, clear button labels (e.g., "Backend", "Python", "def").

After the user watches a lesson, offer quick feedback buttons: "Mark as done", "More like this", "Report problem".

Keep messages short; break long lesson descriptions into bullets.

Short developer checklist (what to implement first)

Database init and simple CRUD functions for categories.

/start and language selection.

/categories listing and keyboard navigation to sub-levels.

Admin validation and add_category flow.

Extend to subcategories → topics → lessons with FSM.

Edit and delete for admin.

Small improvements: URL validation, confirmations, cancel.

Final encouragement (because a little sass is allowed)
Start small with SQLite and a few categories. Make the flows smooth and the admin experience painless — if adding content is easy, your partner will keep the bot fed with lessons and the project will grow itself. Teamwork: you do backend logic and DB, she does the button layout and user flow — perfect duet.