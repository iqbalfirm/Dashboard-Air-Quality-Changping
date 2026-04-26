import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

# halaman utama
st.set_page_config(page_title="Dashboard Kualitas Udara Changping", layout="wide")

DATA_FILE = 'data_harian_Changping.csv'

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df['tanggal'] = pd.to_datetime(df['tanggal'])
    df['Tahun'] = df['tanggal'].dt.year
    df['Bulan'] = df['tanggal'].dt.month_name()
    df['Hari'] = df['tanggal'].dt.day
    return df

try:
    df_mentah = load_data()
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

# sidebar
st.sidebar.header("Filter Data")
pilihan_tahun = st.sidebar.selectbox("Pilih Tahun", sorted(df_mentah['Tahun'].unique()))
df_tahun = df_mentah[df_mentah['Tahun'] == pilihan_tahun]

pilihan_bulan = st.sidebar.selectbox("Pilih Bulan", df_tahun['Bulan'].unique())
df_bulan = df_tahun[df_tahun['Bulan'] == pilihan_bulan]

list_hari = sorted(df_bulan['Hari'].unique())
rentang = st.sidebar.slider("Pilih Rentang Hari", min(list_hari), max(list_hari), (min(list_hari), max(list_hari)))
df_filter = df_bulan[df_bulan['Hari'].between(rentang[0], rentang[1])]

# header
st.title("Dashboard Evaluasi Kualitas Udara Harian Changping")
st.write(f"Periode: **{rentang[0]} - {rentang[1]} {pilihan_bulan} {pilihan_tahun}**")

ambang_batas = {'PM2.5': 55, 'PM10': 75, 'SO2': 75, 'NO2': 65, 'O3': 100, 'CO': 4000}
polutan_tersedia = [p for p in ambang_batas.keys() if p in df_filter.columns]
rata_rata = df_filter[polutan_tersedia].mean()

# KPI Polutan
st.subheader("Rata-rata Intensitas Polutan")
cols = st.columns(len(polutan_tersedia))

for i, polutan in enumerate(polutan_tersedia):
    batas = ambang_batas[polutan]
    nilai = rata_rata[polutan]
    status, warna_delta = ("NORMAL", "normal") if nilai <= batas else ("TINGGI", "inverse")

    cols[i].metric(
        label=f"{polutan} (µg/m³)", 
        value=f"{nilai:.1f}", 
        delta=status, 
        delta_color=warna_delta
    )
    cols[i].caption(f"Batas Aman: **{batas}**")

st.divider()

col_kiri, col_kanan = st.columns([1, 2])

#Status kualitas udara
col_kiri.subheader("Status Kualitas Udara")
if 'Status_Kualitas_Udara' in df_filter.columns:
    tdk_sehat = (df_filter['Status_Kualitas_Udara'] == 'Tidak Sehat').sum()
    col_kiri.success(f"**{len(df_filter) - tdk_sehat} Hari** Normal")
    if tdk_sehat > 0:
        col_kiri.error(f"**{tdk_sehat} Hari** Tidak Sehat")

#Visualisasi
col_kanan.subheader("Tren Konsentrasi Polutan")
option = col_kanan.selectbox("Pilih Polutan:", polutan_tersedia)
batas_aman = ambang_batas[option]

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 4.5))
fig.patch.set_alpha(0); ax.patch.set_alpha(0)

sns.lineplot(data=df_filter, x='tanggal', y=option, marker='o', color="#0064e6", lw=2.5, ax=ax)
ax.fill_between(df_filter['tanggal'], df_filter[option], color="#0064e6", alpha=0.15)

if batas_aman:
    ax.axhline(y=batas_aman, color='#ff5252', ls='--', lw=2, label=f'Batas Aman ({batas_aman})')
    ax.legend(loc='upper right', frameon=False)

ax.set_xticks(df_filter['tanggal'])
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
ax.set_ylabel(f"Konsentrasi ({option}) µg/m³")
ax.set_xlabel("Tanggal (Hari)")
sns.despine()

col_kanan.pyplot(fig, transparent=True)
plt.close(fig)

# Tabel
with st.expander("Lihat Detail Data"):
    df_tabel = df_filter.drop(columns=['Tahun', 'Bulan', 'Hari'])
    warna_map = {'Normal': 'color: #2ecc71; font-weight: bold', 'Tidak Sehat': 'color: #ff5252; font-weight: bold'}
    if 'Status_Kualitas_Udara' in df_tabel.columns:
        df_tabel = df_tabel.style.map(lambda x: warna_map.get(x, ''), subset=['Status_Kualitas_Udara'])
    st.dataframe(df_tabel, use_container_width=True, hide_index=True)