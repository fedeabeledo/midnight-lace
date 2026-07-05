import asyncio
import os
import sys

# Add current directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session
from app.models import Subasta, ItemCatalogo, Catalogo, Producto, Pujo
from sqlalchemy import select, delete

async def main():
    async with async_session() as db:
        # 1. Reset Subasta 1 to 'programada'
        sub = await db.get(Subasta, 1)
        if sub:
            sub.estado = 'programada'
            print("Subasta 1: estado reset to 'programada'")
        else:
            print("Subasta 1 not found")
            return
        
        # 2. Delete all existing bids (pujos) for catalog items to start clean
        catalogo = await db.scalar(select(Catalogo).where(Catalogo.subasta == 1))
        if catalogo:
            result = await db.execute(
                select(ItemCatalogo).where(ItemCatalogo.catalogo == catalogo.identificador)
            )
            items = result.scalars().all()
            for item in items:
                # Delete bids
                await db.execute(delete(Pujo).where(Pujo.item == item.identificador))
                
                # Reset item fields
                item.iniciado_en = None
                item.finalizado_en = None
                item.subastado = 'no'
                
                # Reset product state
                prod = await db.get(Producto, item.producto)
                if prod:
                    prod.estado_producto = 'asignado'
            print("Catalog items, bids, and products reset to defaults.")
        
        await db.commit()
        print("Database transaction committed successfully. Ready for start simulation.")

if __name__ == '__main__':
    asyncio.run(main())
