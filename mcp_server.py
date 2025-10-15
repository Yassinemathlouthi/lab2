# mcp_server.py
import sys
from pathlib import Path
from typing import List, Dict, Optional
from fastmcp import FastMCP

# ensure project root on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ✅ reuse the SQLAlchemy session + ORM from FastAPI app
from main import SessionLocal, ProductORM  # NOT products_db

mcp = FastMCP(name="Product Catalog MCP Server")

def _db():
    return SessionLocal()

@mcp.tool()
def list_products() -> List[Dict]:
    """List products from the MySQL DB (read-only)."""
    with _db() as db:
        items = db.query(ProductORM).order_by(ProductORM.id.asc()).all()
        return [
            {"id": i.id, "name": i.name, "price": i.price, "description": i.description}
            for i in items
        ]

@mcp.tool()
def get_product(product_id: int) -> Dict:
    """Get a single product by ID (read-only)."""
    with _db() as db:
        item: Optional[ProductORM] = db.get(ProductORM, product_id)
        if item:
            return {"id": item.id, "name": item.name, "price": item.price, "description": item.description}
        return {"error": "Product not found", "product_id": product_id}

if __name__ == "__main__":
    mcp.run()
