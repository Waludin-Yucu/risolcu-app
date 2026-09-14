import streamlit as st
from database import get_connection
from datetime import datetime

def halaman_produksi():
    st.title("🍳 Manajemen Resep & Produksi")

    tab1, tab2 = st.tabs(["📝 Form Resep Produk", "⚙️ Eksekusi Produksi"])

    # ==============================
    # TAB 1: FORM RESEP PRODUK
    # ==============================
    with tab1:
        st.subheader("Pengaturan Resep (BOM)")
        conn = get_connection()
        produk_list = conn.execute("SELECT id, nama FROM produk").fetchall()
        bahan_list = conn.execute("SELECT id, nama, satuan FROM bahan_baku").fetchall()
        conn.close()

        if not produk_list or not bahan_list:
            st.warning("Pastikan Anda sudah menginput Data Produk dan Data Bahan Baku terlebih dahulu.")
        else:
            with st.form("form_tambah_resep", clear_on_submit=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    opsi_produk = {p["nama"]: p for p in produk_list}
                    pilihan_p = st.selectbox("Pilih Produk", list(opsi_produk.keys()))
                    p_terpilih = opsi_produk[pilihan_p]

                with col2:
                    opsi_bahan = {f"{b['nama']} ({b['satuan']})": b for b in bahan_list}
                    pilihan_b = st.selectbox("Pilih Bahan Baku", list(opsi_bahan.keys()))
                    b_terpilih = opsi_bahan[pilihan_b]

                with col3:
                    jumlah_butuh = st.number_input(f"Kebutuhan per 1 Pcs", min_value=0.001, step=0.01, format="%.3f")

                submit_resep = st.form_submit_button("Simpan Bahan ke Resep")

                if submit_resep:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO resep (produk_id, bahan_baku_id, jumlah_dibutuhkan)
                            VALUES (?, ?, ?)
                        """, (p_terpilih["id"], b_terpilih["id"], jumlah_butuh))
                        conn.commit()
                        conn.close()
                        st.success(f"Berhasil menambahkan {b_terpilih['nama']} ke resep {p_terpilih['nama']}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan resep: {e}")

            # Tabel Tampil Resep
            st.divider()
            st.subheader("📋 Resep Produk Saat Ini")
            conn = get_connection()
            data_resep = conn.execute("""
                SELECT p.nama as produk, b.nama as bahan, r.jumlah_dibutuhkan, b.satuan
                FROM resep r
                JOIN produk p ON r.produk_id = p.id
                JOIN bahan_baku b ON r.bahan_baku_id = b.id
                ORDER BY p.nama
            """).fetchall()
            conn.close()

            if data_resep:
                tabel_resep = []
                for r in data_resep:
                    tabel_resep.append({
                        "Produk": r["produk"],
                        "Bahan Baku": r["bahan"],
                        "Kebutuhan per 1 Pcs": f"{r['jumlah_dibutuhkan']} {r['satuan']}"
                    })
                st.dataframe(tabel_resep, use_container_width=True)
            else:
                st.info("Belum ada resep terdaftar.")

    # ==============================
    # TAB 2: EKSEKUSI PRODUKSI
    # ==============================
    with tab2:
        st.subheader("Proses Produksi Produk")
        conn = get_connection()
        produk_dengan_resep = conn.execute("""
            SELECT DISTINCT p.id, p.nama 
            FROM produk p 
            JOIN resep r ON p.id = r.produk_id
        """).fetchall()
        conn.close()

        if not produk_dengan_resep:
            st.info("Belum ada produk yang memiliki resep lengkap.")
        else:
            with st.form("form_produksi"):
                opsi_prod = {p["nama"]: p for p in produk_dengan_resep}
                pilihan_prod = st.selectbox("Pilih Produk yang diproduksi", list(opsi_prod.keys()))
                prod_terpilih = opsi_prod[pilihan_prod]

                qty_produksi = st.number_input("Jumlah Produksi (Pcs)", min_value=1, step=1, value=10)
                submit_produksi = st.form_submit_button("🚀 Mulai Produksi")

                if submit_produksi:
                    proses_produksi(prod_terpilih["id"], prod_terpilih["nama"], qty_produksi)

def proses_produksi(produk_id, nama_produk, qty_produksi):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Cek Ketersediaan Stok Bahan Baku
    resep_items = cursor.execute("""
        SELECT r.bahan_baku_id, r.jumlah_dibutuhkan, b.nama, b.stok, b.satuan
        FROM resep r
        JOIN bahan_baku b ON r.bahan_baku_id = b.id
        WHERE r.produk_id = ?
    """, (produk_id,)).fetchall()

    stok_cukup = True
    bahan_kurang = []

    for item in resep_items:
        total_butuh = item["jumlah_dibutuhkan"] * qty_produksi
        if item["stok"] < total_butuh:
            stok_cukup = False
            bahan_kurang.append(f"{item['nama']} (Butuh: {total_butuh} {item['satuan']}, Ada: {item['stok']} {item['satuan']})")

    if not stok_cukup:
        st.error("Gagal produksi! Stok bahan baku tidak mencukupi:")
        for b in bahan_kurang:
            st.write(f"- {b}")
        conn.close()
        return

    # 2. Potong Stok Bahan Baku & Tambah Stok Produk
    try:
        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in resep_items:
            total_butuh = item["jumlah_dibutuhkan"] * qty_produksi
            cursor.execute("""
                UPDATE bahan_baku 
                SET stok = stok - ? 
                WHERE id = ?
            """, (total_butuh, item["bahan_baku_id"]))

        # Tambah Stok Produk Jadi
        cursor.execute("""
            UPDATE produk 
            SET stok = stok + ? 
            WHERE id = ?
        """, (qty_produksi, produk_id))

        # Catat Riwayat Produksi
        cursor.execute("""
            INSERT INTO riwayat_produksi (tanggal, produk_id, jumlah_produksi)
            VALUES (?, ?, ?)
        """, (waktu_sekarang, produk_id, qty_produksi))

        conn.commit()
        conn.close()

        st.success(f"Berhasil memproduksi {qty_produksi} pcs '{nama_produk}'! Stok bahan baku otomatis dipotong dan stok produk bertambah.")
        st.rerun()

    except Exception as e:
        st.error(f"Gagal memproses produksi: {e}")