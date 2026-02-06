import modal
import os

image = (
    modal.Image.debian_slim()
    .pip_install("psycopg2-binary", "sqlalchemy", "sqlmodel")
)

app = modal.App("diag-db")

secrets = modal.Secret.from_dict({
    "DATABASE_URL": "postgresql://neondb_owner:npg_kETgK4j8fUNM@ep-broad-wildflower-ahi897rz-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require",
})

@app.function(image=image, secrets=[secrets])
async def check_db(tx_id: str):
    from sqlalchemy import create_engine, text
    import json
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT id, transaction_type, raw_json FROM transactions WHERE id = '{tx_id}'")).first()
        if res:
            return {
                "id": res[0],
                "transaction_type": res[1],
                "raw_json_summary": json.dumps(res[2])[:300]
            }
        return "Not found"

@app.local_entrypoint()
async def main():
    res = await check_db.remote.aio("115")
    print(res)
