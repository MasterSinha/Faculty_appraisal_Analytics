import os
import sys
from urllib.parse import urlparse, unquote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2

def check_database():
    env_file = ".env"
    if not os.path.exists(env_file):
        print("[ERROR] .env file not found in Backend directory.")
        return

    db_url = None
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.strip().split("=", 1)[1]
                break

    if not db_url:
        print("[ERROR] DATABASE_URL is not set in .env")
        return

    print("Reading DATABASE_URL from .env:")
    print(f"   {db_url}\n")

    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(clean_url)

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    dbname = parsed.path.lstrip("/")

    print("Parsed Connection Parameters:")
    print(f"   Host:     {host}")
    print(f"   Port:     {port}")
    print(f"   User:     {username}")
    print(f"   Database: {dbname}")
    print("=" * 60)

    if host == "host.docker.internal":
        print("[NOTE] 'host.docker.internal' is designed for Docker containers.")
        print("   If running Python directly on Localhost, replace 'host.docker.internal' with:")
        print("   - '127.0.0.1' or 'localhost' (if Postgres is running on your host machine)")
        print("   - Your VM's IP address (e.g. 192.168.x.x) if Postgres is on a Virtual Machine.\n")

    print(f"Attempting connection to {host}:{port}...")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            dbname=dbname,
            connect_timeout=5
        )
        print("[SUCCESS] Connected to PostgreSQL database successfully!\n")
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
        tables = cur.fetchall()
        print(f"Found {len(tables)} tables in 'public' schema:")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM \"{t[0]}\";")
            count = cur.fetchone()[0]
            print(f"   - {t[0]:<35} ({count} rows)")
        conn.close()
        print("\nYour local database configuration is ready to use with the dashboard!")
    except Exception as e:
        print(f"[FAILED] Connection Failed: {e}\n")
        print("Troubleshooting Steps:")
        print("1. If PostgreSQL is on a Virtual Machine (e.g., VMware, VirtualBox, remote server):")
        print("   Update DATABASE_URL in .env with your VM's IP address:")
        print("   DATABASE_URL=postgresql+psycopg2://username:password@<VM_IP_ADDRESS>:5432/<dbname>")
        print("2. Make sure PostgreSQL on the VM accepts remote connections:")
        print("   - postgresql.conf: listen_addresses = '*'")
        print("   - pg_hba.conf: host all all 0.0.0.0/0 md5")
        print("3. Check firewall rules on the VM to ensure port 5432 is open.")

if __name__ == "__main__":
    check_database()
