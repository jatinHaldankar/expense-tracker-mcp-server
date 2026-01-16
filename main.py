from fastmcp import FastMCP
import os
import sqlite3
import aiosqlite

mcp = FastMCP("Expense-tracker")
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
                  subcategory TEXT NOT NULL,
                  note  TEXT DEFAULT ''
                  )
""")

init_db()

@mcp.tool
async def add_expense(date,category,subcategory,amount,note):
    """add a new expense into database."""
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            curr = await c.execute("""
    INSERT INTO expenses(date,amount,category,subcategory="",note="") VALUES (?,?,?,?,?)
    """,(date,amount,category,subcategory,note))
            expense_id = curr.lastrowid
            await c.commit()
            return {"status":"ok","id":expense_id,"message":"Expense Added Successfully"}
    except Exception as e:
        return {"status":"error","message":f"Database Error{str(e)}"}
        

@mcp.tool
def list_expense(start_date,end_date):
    """list the expenses between the start date and the end date."""
    try:
        with aiosqlite.connect(DB_PATH) as c:
            curr = c.execute("SELECT * FROM expenses WHERE date BETWEEN ? AND ?"(start_date,end_date))

            cols = [d[0] for d in curr.description]

            return [dict(zip(cols,row)) for row in curr.fetchall()]
    except Exception as e:
        return {"status":"error","message":f"error while listing the expense {str(e)}"}

@mcp.resource("expense://categories",mime_type="application/json")
def categories():
    
    with open(CATEGORY_PATH,"r",encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run()