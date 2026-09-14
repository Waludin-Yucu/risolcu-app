import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from database import get_connection, init_database

def halaman_laporan():
    init_database()
    st.title("📊 Laporan Penjualan & Riwayat Transaksi")

    conn = get_connection()

    # ==============================
    # 1. FILTER PERIODE WAKTU
    # ==============================
    col_filter, _ = st.columns([2, 2])
    with col_filter:
        periode = st.selectbox(
            "📅 Pilih Periode Laporan:",
            ["Hari Ini", "Pekanan (7 Hari Terakhir)", "Bulanan (Bulan Ini)", "Semua Riwayat"]
        )

    # Query SQL Dasar untuk mengambil data transaksi
    query = """
        SELECT 
            p.id, p.no_nota, p.tanggal, p.total_bayar, p.uang_dibayar, p.kembalian,
            SUM(dp.qty * dp.hpp) as total_hpp
        FROM penjualan p
        LEFT JOIN detail_penjualan dp ON p.id = dp.penjualan_id
    """

    # Filter Berdasarkan Periode
    if periode == "Hari Ini":
        query += " WHERE DATE(p.tanggal) = DATE('now', 'localtime')"
    elif periode == "Pekanan (7 Hari Terakhir)":
        query += " WHERE DATE(p.tanggal) >= DATE('now', '-7 days', 'localtime')"
    elif periode == "Bulanan (Bulan Ini)":
        query += " WHERE strftime('%Y-%m', p.tanggal) = strftime('%Y-%m', 'now', 'localtime')"

    query += " GROUP BY p.id ORDER BY p.tanggal DESC"

    df_penjualan = pd.read_sql_query(query, conn)

    if df_penjualan.empty:
        st.info(f"Belum ada data transaksi penjualan untuk periode: **{periode}**.")
        conn.close()
        return

    # Hitung Laba Bersih per Transaksi
    df_penjualan["laba"] = df_penjualan["total_bayar"] - df_penjualan["total_hpp"].fillna(0)

    # ==============================
    # 2. RINGKASAN METRIK PERIODE
    # ==============================
    total_omset = df_penjualan["total_bayar"].sum()
    total_laba = df_penjualan["laba"].sum()
    total_transaksi = len(df_penjualan)

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Omset", f"Rp {total_omset:,.0f}")
    m2.metric("📈 Est. Laba Bersih", f"Rp {total_laba:,.0f}")
    m3.metric("🧾 Total Transaksi", f"{total_transaksi} Transaksi")

    st.divider()

    # ==============================
    # 3. RIWAYAT & CETAK STRUK
    # ==============================
    st.subheader(f"📜 Riwayat Transaksi ({periode})")

    for _, row in df_penjualan.iterrows():
        penjualan_id = int(row['id'])
        no_nota = row['no_nota']
        tanggal = row['tanggal']
        total_bayar = row['total_bayar']
        uang_dibayar = row['uang_dibayar']
        kembalian = row['kembalian']
        laba_transaksi = row['laba']

        title_expander = f"🧾 {no_nota} | {tanggal} | Total: Rp {total_bayar:,.0f}"

        with st.expander(title_expander):
            # Ambil detail barang transaksi ini
            query_detail = f"""
                SELECT prod.nama as "Nama Produk", dp.qty as "Qty", 
                       dp.harga_jual as "Harga Satuan", dp.subtotal as "Subtotal"
                FROM detail_penjualan dp
                JOIN produk prod ON dp.produk_id = prod.id
                WHERE dp.penjualan_id = {penjualan_id}
            """
            df_detail = pd.read_sql_query(query_detail, conn)

            st.dataframe(df_detail, use_container_width=True)

            c_info, c_btn = st.columns([2, 1])
            with c_info:
                st.write(f"• **Uang Dibayar:** Rp {uang_dibayar:,.0f}")
                st.write(f"• **Kembalian:** Rp {kembalian:,.0f}")
                st.write(f"• **Laba Transaksi Ini:** Rp {laba_transaksi:,.0f}")

            with c_btn:
                # Tombol Cetak Struk
                if st.button("🖨️ Cetak Struk", key=f"print_{penjualan_id}"):
                    html_items = ""
                    for _, item in df_detail.iterrows():
                        html_items += f"""
                        <tr>
                            <td>{item['Nama Produk']}<br><small>{item['Qty']} x {item['Harga Satuan']:,.0f}</small></td>
                            <td style="text-align:right; vertical-align:bottom;">{item['Subtotal']:,.0f}</td>
                        </tr>
                        """

                    html_code = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            body {{ font-family: monospace; width: 280px; font-size: 12px; margin: 0; padding: 10px; }}
                            .text-center {{ text-align: center; }}
                            .text-right {{ text-align: right; }}
                            hr {{ border-top: 1px dashed #000; }}
                            table {{ width: 100%; font-size: 12px; border-collapse: collapse; }}
                        </style>
                    </head>
                    <body>
                        <div class="text-center">
                            <h2 style="margin:0;">🥟 RISOLCU</h2>
                            <p style="margin:2px 0;">Jl. Contoh No. 123<br>Telp: 0812-3456-7890</p>
                        </div>
                        <hr>
                        <p style="margin:2px 0;">Nota : {no_nota}<br>Tgl  : {tanggal}</p>
                        <hr>
                        <table>{html_items}</table>
                        <hr>
                        <table>
                            <tr><td><b>Total</b></td><td class="text-right"><b>Rp {total_bayar:,.0f}</b></td></tr>
                            <tr><td>Bayar</td><td class="text-right">Rp {uang_dibayar:,.0f}</td></tr>
                            <tr><td>Kembali</td><td class="text-right">Rp {kembalian:,.0f}</td></tr>
                        </table>
                        <hr>
                        <div class="text-center"><p>-- Terima Kasih --</p></div>
                        <script>window.onload = function() {{ window.print(); }}</script>
                    </body>
                    </html>
                    """
                    components.html(html_code, height=0, width=0)

    conn.close()