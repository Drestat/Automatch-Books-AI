import modal
import os
from dotenv import dotenv_values

base_dir = os.path.dirname(os.path.abspath(__file__))
image = (
    modal.Image.debian_slim()
    .pip_install("sqlalchemy", "psycopg2-binary", "python-dotenv", "pydantic-settings", "alembic")
    .add_local_dir(os.path.join(base_dir, "app"), remote_path="/root/app")
    .add_local_dir(os.path.join(base_dir, "alembic"), remote_path="/root/alembic")
    .copy_local_file(os.path.join(base_dir, "alembic.ini"), "/root/alembic.ini")
)
app = modal.App("run-migration")
secrets = modal.Secret.from_dict({"DATABASE_URL": dotenv_values(os.path.join(base_dir, ".env")).get("DATABASE_URL", "")})

@app.function(image=image, secrets=[secrets])
def run_migration():
    import subprocess
    import os
    
    print("Running Alembic migration...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="/root",
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Migration failed with exit code {result.returncode}")
    else:
        print("✅ Migration completed successfully!")

if __name__ == "__main__":
    pass
