import asyncio
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session
from app.services import pujas as pujas_service
from app.models import Pujo, ItemCatalogo, Catalogo
from sqlalchemy import select

async def main():
    async with async_session() as db:
        p_res = await db.execute(select(Pujo).limit(1))
        puja = p_res.scalars().first()
        if not puja:
            print("No bids found.")
            return
            
        item = await db.get(ItemCatalogo, puja.item)
        catalogo = await db.get(Catalogo, item.catalogo)
        
        print(f"Testing with Subasta: {catalogo.subasta}, Item: {item.identificador}")
        res = await pujas_service.historial_pujas(db, catalogo.subasta, item.identificador, 1, 10)
        print("Raw Service Response:")
        print(json.dumps(res, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
