import streamlit as st
import pandas as pd
from database import get_connection, init_database
from datetime import datetime

def halaman_produk():
    init_database()
    st.title("📦 Kelola Produk & Riwayat Stok")

    conn = get_connection()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Daftar Produk", 
        "🔄 Restock Produk", 
        "📊 Riwayat Alur Stok", 
        "➕ Produk Baru"
    ])

    # ==============================
    # TAB 1: DAFTAR PRODUK
    # ==============================
    with tab1:
        st.subheader("Daftar Produk & Stok Saat Ini")
        df_produk = pd.read_sql_query("SELECT id, kode, nama, hpp, harga_jual, stok FROM produk ORDER BY nama ASC", conn)
        
        if df_produk.empty:
            st.info("Belum ada data produk.")
        else:
            st.dataframe(df_produk, use_container_width=True)

    # ==============================
    # TAB 2: RESTOCK / TAMBAH STOK
    # ==============================
    with tab2:
        st.subheader("Tambah Stok Produk Lama (Restock)")
        produk_list = conn.execute("SELECT id, nama, stok FROM produk ORDER BY nama ASC").fetchall()

        if not produk_list:
            st.warning("Belum ada produk yang tersimpan.")
        else:
            opsi_produk = {f"{p['nama']} (Stok Saat Ini: {p['stok']})": p for p in produk_list}
            pilihan_restock = st.selectbox("Pilih Produk", list(opsi_produk.keys()))
            produk_terpilih = opsi_produk[pilihan_restock]

            with st.form("form_restock"):
                stok_tambahan = st.number_input("Jumlah Stok Tambahan", min_value=1, step=1, value=1)
                keterangan = st.text_input("Keterangan Restock", value="Restock / Pembelian Stok Baru")
                submit_restock = st.form_submit_button("🔄 Restock Stok")

                if submit_restock:
                    try:
                        cursor = conn.cursor()
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # 1. Update Stok di Produk
                        cursor.execute("UPDATE produk SET stok = stok + ? WHERE id = ?", (stok_tambahan, produk_terpilih["id"]))
                        
                        # 2. Catat Riwayat Stok Masuk
                        cursor.execute("""
                            INSERT INTO riwayat_stok (produk_id, tipe, jumlah, keterangan, tanggal)
                            VALUES (?, 'MASUK', ?, ?, ?)
                        """, (produk_terpilih["id"], stok_tambahan, keterangan, now))

                        conn.commit()
                        st.success(f"Berhasil menambahkan {stok_tambahan} pcs stok ke '{produk_terpilih['nama']}'.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal mengupdate stok: {e}")

    # ==============================
    # TAB 3: RIWAYAT ALUR STOK (HARIAN, PEKANAN, BULANAN)
    # ==============================
    with tab3:
        st.subheader("📈 Riwayat Alur Masuk & Keluar Stok")

        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            periode = st.selectbox(
                "📅 Pilih Periode Filter:",
                ["Hari Ini", "Pekanan (7 Hari Terakhir)", "Bulanan (Bulan Ini)", "Semua Riwayat"]
            )
        with col_f2:
            filter_tipe = st.selectbox("🔄 Tipe Alur:", ["Semua (MASUK & KELUAR)", "MASUK Saja", "KELUAR Saja"])

        # Query Dasar
        query_stok = """
            SELECT 
                r.tanggal as "Waktu",
                p.nama as "Nama Produk",
                r.tipe as "Tipe Alur",
                r.jumlah as "Jumlah (Pcs)",
                r.keterangan as "Keterangan"
            FROM riwayat_stok r
            JOIN produk p ON r.produk_id = p.id
        """

        conditions = []

        # Filter Periode Waktu
        if periode == "Hari Ini":
            conditions.append("DATE(r.tanggal) = DATE('now', 'localtime')")
        elif periode == "Pekanan (7 Hari Terakhir)":
            conditions.append("DATE(r.tanggal) >= DATE('now', '-7 days', 'localtime')")
        elif periode == "Bulanan (Bulan Ini)":
            conditions.append("strftime('%Y-%m', r.tanggal) = strftime('%Y-%m', 'now', 'localtime')")

        # Filter Tipe Alur
        if filter_tipe == "MASUK Saja":
            conditions.append("r.tipe = 'MASUK'")
        elif filter_tipe == "KELUAR Saja":
            conditions.append("r.tipe = 'KELUAR'")

        if conditions:
            query_stok += " WHERE " + " AND ".join(conditions)

        query_stok += " ORDER BY r.tanggal DESC"

        df_riwayat = pd.read_sql_query(query_stok, conn)

        if df_riwayat.empty:
            st.info(f"Belum ada riwayat alur stok untuk periode: **{periode}**.")
        else:
            # Hitung Ringkasan Masuk & Keluar
            total_masuk = df_riwayat[df_riwayat["Tipe Alur"] == "MASUK"]["Jumlah (Pcs)"].sum()
            total_keluar = df_riwayat[df_riwayat["Tipe Alur"] == "KELUAR"]["Jumlah (Pcs)"].sum()

            m1, m2 = st.columns(2)
            m1.metric("📥 Total Stok MASUK", f"{total_masuk} Pcs")
            m2.metric("📤 Total Stok KELUAR", f"{total_keluar} Pcs")

            st.divider()
            st.dataframe(df_riwayat, use_container_width=True)

    # ==============================
    # TAB 4: TAMBAH PRODUK BARU
    # ==============================
    with tab4:
        st.subheader("Tambah Produk Baru")
        with st.form("form_tambah_produk"):
            kode = st.text_input("Kode Produk (Opsional/Barcode)")
            nama = st.text_input("Nama Produk *")
            hpp = st.number_input("HPP / Modal (Rp) *", min_value=0.0, step=500.0)
            harga_jual = st.number_input("Harga Jual (Rp) *", min_value=0.0, step=500.0)
            stok_awal = st.number_input("Stok Awal *", min_value=0, step=1)

            submit = st.form_submit_button("💾 Simpan Produk Baru")

            if submit:
                if not nama:
                    st.error("Nama produk wajib diisi!")
                else:
                    try:
                        cursor = conn.cursor()
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # Simpan Produk Baru
                        cursor.execute("""
                            INSERT INTO produk (kode, nama, hpp, harga_jual, stok)
                            VALUES (?, ?, ?, ?, ?)
                        """, (kode, nama, hpp, harga_jual, stok_awal))
                        
                        produk_id = cursor.lastrowid

                        # Catat Stok Awal sebagai MASUK
                        if stok_awal > 0:
                            cursor.execute("""
                                INSERT INTO riwayat_stok (produk_id, tipe, jumlah, keterangan, tanggal)
                                VALUES (?, 'MASUK', ?, 'Stok Awal Produk Baru', ?)
                            """, (produk_id, stok_awal, now))

                        conn.commit()
                        st.success(f"Produk '{nama}' berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambahkan produk: {e}")

    conn.close()