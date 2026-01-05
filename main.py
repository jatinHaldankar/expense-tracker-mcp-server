from fastmcp import FastMCP
import sqlite3
import aiosqlite
import os

mcp = FastMCP(name="demo-server")
DB_PATH = os.path.join(os.path.dirname(__file__),"expense.db")
CATEGORY_PATH = os.path.join(os.path.dirname(__file__),"categories.json")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL,
                  amount REAL NOT NULL,
                  category TEXT NOT NULL,
                  subcategory TEXT DEFAULT '',
                  note TEXT DEFAULT ''
                )
""")

init_db()

@mcp.tool()
async def add_expense(date,amount,category,subcategory="",note=""):
    """add a new expense into database."""
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            curr = await c.execute("INSERT INTO expenses(date,amount,category,subcategory,note) VALUES(?,?,?,?,?)", (date,amount,category,subcategory,note))

            expense_id = curr.lastrowid
            await c.commit()
        return {"status":"ok","id": expense_id, "message":"Expenses Added Successfully."}
    except Exception as e:
        return {"status":"error","message":"Database Error {e}"}


@mcp.tool()
async def list_expense(start_date,end_date):
    """list the expenses between start and end date"""
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            curr = await c.execute("""SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY id ASC""",(start_date,end_date))

            cols = [d[0] for d in curr.description]
            return [dict(zip(cols,row)) for row in curr.fetchall()]
    except Exception as e:
        return {"status":"error","message":"not able to insert in database. {e}"}



@mcp.tool()
async def summarize(start_date,end_date,category=None):
    """summarize the expenses between start and end date."""
    try:
        async with sqlite3.connect(DB_PATH) as c:
            query = """SELECT category,SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?"""

            params = [start_date,end_date]
        
            if category:
                query += "AND category = ?"
                params.append(category)
            
            query += "GROUP BY category ORDER BY category ASC"

            curr = await c.execute(query,params)
            cols = [d[0] for d in curr.description]
            return [dict(zip(cols,rows)) for rows in curr.fetchall()]
    except Exception as e:
        return {"status":"error","message":"not able to summarize the messages."}

@mcp.resource("expense://categories",mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORY_PATH,"r",encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run()
