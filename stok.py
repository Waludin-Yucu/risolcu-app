import streamlit as st
from database import get_connection
import sqlite3

def halaman_stok():
    st.title("📦 Manajemen Stok Bahan Baku")

    col_tambah, col_update = st.columns([1, 1])

    # ==============================
    # 1. TAMBAH BAHAN BAKU BARU
    # ==============================
    with col_tambah:
        with st.expander("➕ Tambah Bahan Baku Baru", expanded=True):
            with st.form("form_tambah_bahan", clear_on_submit=True):
                nama_bahan = st.text_input("Nama Bahan (contoh: Tepung Terigu)").strip()
                satuan = st.selectbox("Satuan", ["kg", "gram", "liter", "ml", "pcs", "bks"])
                stok_awal = st.number_input("Stok Awal", min_value=0.0, step=0.1, value=0.0)
                harga_satuan = st.number_input("Harga per Satuan (Rp)", min_value=0.0, step=500.0, value=10000.0)

                submitted = st.form_submit_button("Simpan Bahan Baku")

                if submitted:
                    if not nama_bahan:
                        st.error("Nama bahan baku tidak boleh kosong!")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO bahan_baku (nama, satuan, stok, harga_per_satuan)
                                VALUES (?, ?, ?, ?)
                            """, (nama_bahan, satuan, stok_awal, harga_satuan))
                            conn.commit()
                            conn.close()
                            st.success(f"Bahan baku '{nama_bahan}' berhasil ditambahkan!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"Bahan baku '{nama_bahan}' sudah ada!")
                        except Exception as e:
                            st.error(f"Gagal menyimpan: {e}")

    # ==============================
    # 2. REFILL / RESTOK BAHAN BAKU
    # ==============================
    with col_update:
        with st.expander("📥 Restok / Tambah Stok Bahan", expanded=True):
            conn = get_connection()
            list_bahan = conn.execute("SELECT id, nama, satuan FROM bahan_baku").fetchall()
            conn.close()

            if list_bahan:
                with st.form("form_refill_bahan", clear_on_submit=True):
                    opsi_bahan = {f"{b['nama']} ({b['satuan']})": b for b in list_bahan}
                    pilihan = st.selectbox("Pilih Bahan Baku", list(opsi_bahan.keys()))
                    bahan_terpilih = opsi_bahan[pilihan]

                    tambah_stok = st.number_input("Jumlah Tambahan Stok", min_value=0.1, step=0.5, value=1.0)
                    submit_refill = st.form_submit_button("Update Stok")

                    if submit_refill:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE bahan_baku 
                                SET stok = stok + ? 
                                WHERE id = ?
                            """, (tambah_stok, bahan_terpilih["id"]))
                            conn.commit()
                            conn.close()
                            st.success(f"Stok '{bahan_terpilih['nama']}' berhasil ditambah!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal memperbarui stok: {e}")
            else:
                st.info("Belum ada bahan baku terdaftar.")

    # ==============================
    # 3. TABEL DAFTAR BAHAN BAKU
    # ==============================
    st.subheader("📋 Daftar Stok Bahan Baku")
    conn = get_connection()
    bahan_baku = conn.execute("SELECT id, nama, satuan, stok, harga_per_satuan FROM bahan_baku").fetchall()
    conn.close()

    if bahan_baku:
        data_tabel = []
        for b in bahan_baku:
            data_tabel.append({
                "ID": b["id"],
                "Nama Bahan": b["nama"],
                "Stok Saat Ini": f"{b['stok']:,} {b['satuan']}",
                "Harga / Satuan": f"Rp{b['harga_per_satuan']:,}"
            })
        st.dataframe(data_tabel, use_container_width=True)
    else:
        st.info("Belum ada data stok bahan baku.")