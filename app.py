import streamlit as st
from database import init_database
from produk import halaman_produk
from kasir import halaman_kasir
from laporan import halaman_laporan
from stok import halaman_stok
from produksi import halaman_produksi
from forecasting import halaman_forecasting  # ← Import modul forecasting

init_database()

st.set_page_config(page_title="Risolcu Kasir", page_icon="🥟", layout="wide")
st.sidebar.title("🥟 RISOLCU")

menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Produk", "Kasir", "Stok", "Produksi", "Laporan", "Forecasting"]
)

if menu == "Dashboard":
    st.title("🥟 Risolcu Kasir")
    st.subheader("Dashboard")
    st.info("Selamat datang di sistem kasir Risolcu.")
elif menu == "Produk":
    halaman_produk()
elif menu == "Kasir":
    halaman_kasir()
elif menu == "Stok":
    halaman_stok()
elif menu == "Produksi":
    halaman_produksi()
elif menu == "Laporan":
    halaman_laporan()
elif menu == "Forecasting":
    halaman_forecasting()  # ← Panggil halaman forecasting