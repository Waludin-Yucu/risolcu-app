import streamlit as st
import streamlit.components.v1 as components
from database import get_connection, init_database
from datetime import datetime

def halaman_kasir():
    init_database()
    st.title("🛒 Kasir Risolcu")

    if "keranjang" not in st.session_state:
        st.session_state.keranjang = []

    conn = get_connection()
    produk_list = conn.execute("SELECT * FROM produk WHERE stok > 0").fetchall()
    conn.close()

    col_kiri, col_kanan = st.columns([1, 1])

    with col_kiri:
        st.subheader("Pilih Produk")
        if not produk_list:
            st.warning("Belum ada produk atau stok semua produk kosong.")
        else:
            opsi_produk = {f"{p['nama']} (Stok: {p['stok']}) - Rp{p['harga_jual']:,.0f}": p for p in produk_list}
            pilihan = st.selectbox("Produk", list(opsi_produk.keys()))
            produk_terpilih = opsi_produk[pilihan]

            qty = st.number_input("Jumlah (Qty)", min_value=1, max_value=produk_terpilih["stok"], value=1)

            if st.button("➕ Tambah ke Keranjang"):
                ada = False
                for item in st.session_state.keranjang:
                    if item["id"] == produk_terpilih["id"]:
                        if item["qty"] + qty > produk_terpilih["stok"]:
                            st.error("Jumlah melebihi stok yang tersedia!")
                        else:
                            item["qty"] += qty
                            item["subtotal"] = item["qty"] * item["harga_jual"]
                            st.success("Jumlah produk diperbarui!")
                        ada = True
                        break

                if not ada:
                    st.session_state.keranjang.append({
                        "id": produk_terpilih["id"],
                        "kode": produk_terpilih["kode"],
                        "nama": produk_terpilih["nama"],
                        "harga_jual": produk_terpilih["harga_jual"],
                        "hpp": produk_terpilih["hpp"],
                        "qty": qty,
                        "subtotal": qty * produk_terpilih["harga_jual"]
                    })
                    st.success("Berhasil masuk keranjang!")

    with col_kanan:
        st.subheader("📋 Keranjang Belanja")

        if not st.session_state.keranjang:
            st.info("Keranjang masih kosong.")
        else:
            total_bayar = sum(item["subtotal"] for item in st.session_state.keranjang)
            
            for idx, item in enumerate(st.session_state.keranjang):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                c1.write(item["nama"])
                c2.write(f"{item['qty']} x Rp {item['harga_jual']:,.0f}")
                c3.write(f"Rp {item['subtotal']:,.0f}")
                if c4.button("❌", key=f"del_{idx}"):
                    st.session_state.keranjang.pop(idx)
                    st.rerun()

            st.divider()
            st.markdown(f"### **Total: Rp {total_bayar:,.0f}**")

            uang_dibayar = st.number_input("Uang Dibayar (Rp)", min_value=0.0, value=float(total_bayar), step=1000.0)
            kembalian = uang_dibayar - total_bayar

            if kembalian < 0:
                st.warning(f"Uang kurang: Rp {abs(kembalian):,.0f}")
            else:
                st.info(f"Kembalian: Rp {kembalian:,.0f}")

            if st.button("🔴 Reset Keranjang"):
                st.session_state.keranjang = []
                st.rerun()

            if st.button("✅ Selesaikan Transaksi", type="primary"):
                if uang_dibayar < total_bayar:
                    st.error("Uang pembayaran kurang!")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        no_nota = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        cursor.execute("""
                            INSERT INTO penjualan (no_nota, tanggal, total_bayar, uang_dibayar, kembalian)
                            VALUES (?, ?, ?, ?, ?)
                        """, (no_nota, tanggal, total_bayar, uang_dibayar, kembalian))
                        
                        penjualan_id = cursor.lastrowid

                        for item in st.session_state.keranjang:
                            cursor.execute("""
                                INSERT INTO detail_penjualan (penjualan_id, produk_id, harga_jual, hpp, qty, subtotal)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (penjualan_id, item["id"], item["harga_jual"], item["hpp"], item["qty"], item["subtotal"]))

                            # Potong Stok
                            cursor.execute("UPDATE produk SET stok = stok - ? WHERE id = ?", (item["qty"], item["id"]))

                            # Catat Riwayat Stok Keluar
                            cursor.execute("""
                                INSERT INTO riwayat_stok (produk_id, tipe, jumlah, keterangan, tanggal)
                                VALUES (?, 'KELUAR', ?, ?, ?)
                            """, (item["id"], item["qty"], f"Penjualan Nota: {no_nota}", tanggal))

                        conn.commit()
                        conn.close()

                        st.session_state.last_nota = {
                            "no_nota": no_nota,
                            "tanggal": tanggal,
                            "items": st.session_state.keranjang.copy(),
                            "total_bayar": total_bayar,
                            "uang_dibayar": uang_dibayar,
                            "kembalian": kembalian
                        }

                        st.session_state.keranjang = []
                        st.rerun()

                    except Exception as e:
                        st.error(f"Gagal memproses transaksi: {e}")

    if "last_nota" in st.session_state and st.session_state.last_nota:
        nota = st.session_state.last_nota
        st.divider()
        st.success(f"🎉 Transaksi Berhasil! No Nota: **{nota['no_nota']}**")

        c_cetak1, c_cetak2 = st.columns([1, 2])
        with c_cetak1:
            if st.button("🖨️ CETAK STRUK SEKARANG", type="primary"):
                html_items = ""
                for itm in nota['items']:
                    html_items += f"""
                    <tr>
                        <td>{itm['nama']}<br><small>{itm['qty']} x {itm['harga_jual']:,.0f}</small></td>
                        <td style="text-align:right; vertical-align:bottom;">{itm['subtotal']:,.0f}</td>
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
                    <p style="margin:2px 0;">Nota : {nota['no_nota']}<br>Tgl  : {nota['tanggal']}</p>
                    <hr>
                    <table>{html_items}</table>
                    <hr>
                    <table>
                        <tr><td><b>Total</b></td><td class="text-right"><b>Rp {nota['total_bayar']:,.0f}</b></td></tr>
                        <tr><td>Bayar</td><td class="text-right">Rp {nota['uang_dibayar']:,.0f}</td></tr>
                        <tr><td>Kembali</td><td class="text-right">Rp {nota['kembalian']:,.0f}</td></tr>
                    </table>
                    <hr>
                    <div class="text-center"><p>-- Terima Kasih --</p></div>
                    <script>window.onload = function() {{ window.print(); }}</script>
                </body>
                </html>
                """
                components.html(html_code, height=0, width=0)

        with c_cetak2:
            if st.button("❌ Selesai / Transaksi Baru"):
                del st.session_state.last_nota
                st.rerun()