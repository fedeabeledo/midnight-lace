import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session
from app.models import ItemCatalogo
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(ItemCatalogo).where(ItemCatalogo.producto == 2))
        item = res.scalars().first()
        if item:
            print(f"Product 2 is Item ID: {item.identificador} in Catalog: {item.catalogo}")
        else:
            print("Product 2 is not in any catalog.")

if __name__ == '__main__':
    asyncio.run(main())
