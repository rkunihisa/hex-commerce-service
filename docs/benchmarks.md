# Day 10 Benchmarks (baseline notes)

Environment
- DB: Postgres 16 (docker-compose)
- SQLAlchemy: 2.x (async), driver: asyncpg
- Machine: [fill your CPU/RAM]
- Dataset: 200 orders x 5 lines each (1,000 lines)

Results (sample; update with your runs)
- list orders (selectinload lines): ~XX ms
- queries executed: 2 (orders + order_lines via selectinload)

Notes
- Indexes added (0002_add_indexes):
  - orders: (created_at), (currency, created_at)
  - order_lines: (sku), (order_id, sku)
  - inventory_items: (sku)
- Ensure repository uses selectinload when listing orders to avoid N+1.
