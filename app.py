import streamlit as st
import pandas as pd
from database import get_connection, init_database
import stok
import produksi
import kasir

# Set konfigurasi halaman
st.set_page_config(
    page_title="POS Risolcu",
    page_icon="🥐",
    layout="wide"
)

# Inisialisasi Database saat aplikasi pertama kali dimuat
init_database()

def tampilan_dashboard():
    st.title("📊 Dashboard & Analytics Penjualan")
    st.write("Ringkasan performa bisnis dan statistik penjualan Risolcu.")

    conn = get_connection()

    # --- 1. RINGKASAN METRIK (KPI CARDS) ---
    col1, col2, col3, col4 = st.columns(4)

    # Total Omset / Penjualan
    df_omset = pd.read_sql_query("SELECT SUM(total_bayar) as total FROM penjualan", conn)
    total_omset = df_omset['total'].iloc[0] if df_omset['total'].iloc[0] is not None else 0

    # Total Transaksi
    df_trx = pd.read_sql_query("SELECT COUNT(*) as total FROM penjualan", conn)
    total_trx = df_trx['total'].iloc[0]

    # Total Keuntungan (Profit HPP)
    df_profit = pd.read_sql_query("""
        SELECT SUM(subtotal - (hpp * qty)) as total_profit 
        FROM detail_penjualan
    """, conn)
    total_profit = df_profit['total_profit'].iloc[0] if df_profit['total_profit'].iloc[0] is not None else 0

    # Total Produk Terjual (Qty)
    df_qty = pd.read_sql_query("SELECT SUM(qty) as total_qty FROM detail_penjualan", conn)
    total_qty = df_qty['total_qty'].iloc[0] if df_qty['total_qty'].iloc[0] is not None else 0

    col1.metric("💰 Total Omset", f"Rp {total_omset:,.0f}")
    col2.metric("📦 Produk Terjual", f"{total_qty:,} pcs")
    col3.metric("🧾 Total Transaksi", f"{total_trx:,} Nota")
    col4.metric("📈 Estimasi Keuntungan", f"Rp {total_profit:,.0f}")

    st.divider()

    # --- 2. GRAFIK PENJUALAN ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📈 Tren Omset Penjualan (Harian)")
        # Mengambil data omset per tanggal
        query_tren = """
            SELECT DATE(tanggal) as Tanggal, SUM(total_bayar) as Total_Omset
            FROM penjualan
            GROUP BY DATE(tanggal)
            ORDER BY DATE(tanggal) ASC
        """
        df_tren = pd.read_sql_query(query_tren, conn)

        if not df_tren.empty:
            df_tren['Tanggal'] = pd.to_datetime(df_tren['Tanggal'])
            df_tren = df_tren.set_index('Tanggal')
            # Menampilkan Line Chart Streamlit
            st.line_chart(df_tren, use_container_width=True)
        else:
            st.info("Belum ada data penjualan untuk menampilkan grafik tren.")

    with col_chart2:
        st.subheader("🏆 Produk Terlaris (Top Selling)")
        # Mengambil data total item terjual per produk
        query_top = """
            SELECT p.nama as Nama_Produk, SUM(dp.qty) as Terjual
            FROM detail_penjualan dp
            JOIN produk p ON dp.produk_id = p.id
            GROUP BY p.id
            ORDER BY Terjual DESC
            LIMIT 5
        """
        df_top = pd.read_sql_query(query_top, conn)

        if not df_top.empty:
            df_top = df_top.set_index('Nama_Produk')
            # Menampilkan Bar Chart Streamlit
            st.bar_chart(df_top, use_container_width=True)
        else:
            st.info("Belum ada data detail transaksi.")

    st.divider()

    # --- 3. TABEL RIWAYAT TRANSAKSI TERAKHIR ---
    st.subheader("📋 5 Transaksi Terakhir")
    df_recent = pd.read_sql_query("""
        SELECT no_nota as "No. Nota", tanggal as "Tanggal & Waktu", 
               total_bayar as "Total (Rp)", uang_dibayar as "Bayar (Rp)", kembalian as "Kembali (Rp)"
        FROM penjualan 
        ORDER BY id DESC LIMIT 5
    """, conn)

    if not df_recent.empty:
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("Belum ada riwayat transaksi.")

    conn.close()

# --- SIDESBAR NAVIGATION ---
st.sidebar.title("🥐 Risolcu POS")
menu = st.sidebar.radio(
    "Navigasi Utama",
    ["📊 Dashboard", "🛒 Kasir (POS)", "🧱 Stok & Bahan", "🏭 Produksi"]
)

if menu == "📊 Dashboard":
    tampilan_dashboard()
elif menu == "🛒 Kasir (POS)":
    if hasattr(kasir, 'halaman_kasir'):
        kasir.halaman_kasir()
    else:
        st.info("Halaman Kasir sedang dimuat...")
elif menu == "🧱 Stok & Bahan":
    if hasattr(stok, 'halaman_stok'):
        stok.halaman_stok()
    else:
        st.info("Halaman Stok sedang dimuat...")
elif menu == "🏭 Produksi":
    if hasattr(produksi, 'halaman_produksi'):
        produksi.halaman_produksi()
    else:
        st.info("Halaman Produksi sedang dimuat...")
