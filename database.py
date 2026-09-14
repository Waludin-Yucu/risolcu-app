import sqlite3

DATABASE_NAME = "pos_risolcu.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Fungsi ini otomatis membuat tabel baru & memperbarui struktur tabel yang kurang."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabel Produk
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode TEXT,
            nama TEXT NOT NULL,
            hpp REAL NOT NULL DEFAULT 0,
            harga_jual REAL NOT NULL DEFAULT 0,
            stok INTEGER NOT NULL DEFAULT 0
        )
    """)

    # 2. Tabel Penjualan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS penjualan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no_nota TEXT NOT NULL,
            tanggal DATETIME NOT NULL,
            total_bayar REAL NOT NULL,
            uang_dibayar REAL NOT NULL,
            kembalian REAL NOT NULL
        )
    """)

    # 3. Tabel Detail Penjualan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detail_penjualan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            penjualan_id INTEGER NOT NULL,
            produk_id INTEGER NOT NULL,
            harga_jual REAL NOT NULL,
            hpp REAL NOT NULL,
            qty INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (penjualan_id) REFERENCES penjualan(id),
            FOREIGN KEY (produk_id) REFERENCES produk(id)
        )
    """)

    # 4. Tabel Riwayat Stok Produk
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS riwayat_stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produk_id INTEGER NOT NULL,
            tipe TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            keterangan TEXT,
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produk_id) REFERENCES produk(id)
        )
    """)

    # 5. Tabel Bahan Baku
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bahan_baku (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            stok REAL NOT NULL DEFAULT 0,
            satuan TEXT NOT NULL,
            harga_per_satuan REAL DEFAULT 0
        )
    """)

    # 6. Tabel Resep (BOM)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produk_id INTEGER NOT NULL,
            bahan_id INTEGER NOT NULL,
            jumlah_butuh REAL NOT NULL,
            FOREIGN KEY (produk_id) REFERENCES produk(id),
            FOREIGN KEY (bahan_id) REFERENCES bahan_baku(id)
        )
    """)

    # 7. Tabel Produksi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produk_id INTEGER NOT NULL,
            jumlah_produksi INTEGER NOT NULL,
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produk_id) REFERENCES produk(id)
        )
    """)

    conn.commit()
    conn.close()