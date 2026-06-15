import aiosqlite

DB_NAME = os.getenv("DB_NAME", "crm.db")


# =====================
# INIT DB
# =====================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                event_date TEXT,
                status TEXT DEFAULT 'new',
                taken_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


# =====================
# ADD ORDER
# =====================
async def add_order(name, phone, event_date, status="new"):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO orders (name, phone, event_date, status)
            VALUES (?, ?, ?, ?)
        """, (name, phone, event_date, status))

        await db.commit()
        return cursor.lastrowid


# =====================
# UPDATE STATUS
# =====================
async def update_status(order_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """, (status, order_id))

        await db.commit()


# =====================
# UPDATE WHO TOOK ORDER
# =====================
async def update_taken_by(order_id, admin_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE orders
            SET taken_by = ?
            WHERE id = ?
        """, (admin_name, order_id))

        await db.commit()


# =====================
# GET ORDER
# =====================
async def get_order(order_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT id, name, phone, event_date, status, taken_by
            FROM orders
            WHERE id = ?
        """, (order_id,))

        return await cursor.fetchone()