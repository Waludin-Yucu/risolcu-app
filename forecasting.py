import streamlit as st
import pandas as pd
from database import get_connection, init_database

def halaman_forecasting():
    init_database()
    st.title("🔮 Forecasting & Prediksi Kebutuhan Stok")

    conn = get_connection()
    # Ambil data histori penjualan harian per produk
    query = """
        SELECT 
            DATE(p.tanggal) as tanggal,
            prod.nama as nama_produk,
            SUM(dp.qty) as total_qty
        FROM detail_penjualan dp
        JOIN penjualan p ON dp.penjualan_id = p.id
        JOIN produk prod ON dp.produk_id = prod.id
        GROUP BY DATE(p.tanggal), prod.nama
        ORDER BY tanggal ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.info("Belum ada data transaksi penjualan yang cukup untuk melakukan forecasting. Silakan lakukan transaksi di menu Kasir terlebih dahulu.")
        return

    st.subheader("📊 Histori Penjualan Harian")
    st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("📈 Prediksi Kebutuhan Produksi Harian (Simple Moving Average)")

    # Pilihan window hari untuk moving average
    window_days = st.slider("Jumlah Hari Acuan (Moving Average Window)", min_value=3, max_value=30, value=7)

    # Hitung prediksi per produk
    produk_list = df['nama_produk'].unique()
    hasil_prediksi = []

    for prod in produk_list:
        df_prod = df[df['nama_produk'] == prod].copy()
        df_prod['tanggal'] = pd.to_datetime(df_prod['tanggal'])
        df_prod = df_prod.sort_values('tanggal')

        # Hitung rata-rata penjualan harian berdasarkan window_days
        rata_rata_harian = df_prod['total_qty'].tail(window_days).mean()
        
        # Rekomendasi stok aman (Safety Stock = 20% dari prediksi)
        prediksi_hari_ini = int(round(rata_rata_harian))
        safety_stock = int(round(prediksi_hari_ini * 0.2))
        total_rekomendasi = prediksi_hari_ini + safety_stock

        hasil_prediksi.append({
            "Nama Produk": prod,
            f"Rata-rata Penjualan ({window_days} Hari Terakhir)": f"{rata_rata_harian:.1f} pcs/hari",
            "Est. Penjualan Besok": f"{prediksi_hari_ini} pcs",
            "Safety Stock (20%)": f"{safety_stock} pcs",
            "Rekomendasi Produksi": f"**{total_rekomendasi} pcs**"
        })

    st.dataframe(hasil_prediksi, use_container_width=True)

    st.caption("💡 **Catatan:** Rekomendasi produksi dihitung dari rata-rata penjualan harian ditambah cadangan aman (*safety stock*) 20%.")