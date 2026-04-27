import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

# HEADER UTAMA
st.title("Dashboard Kualitas Udara Changping")

tab1, tab2 = st.tabs(["Ringkasan Harian", "Analisis Pola Waktu"])

# KONFIGURASI HALAMAN
st.set_page_config(page_title="Dashboard Kualitas Udara Changping", layout="wide")
DATA_POLUSI = "data_polusi.csv"

NAMA_BULAN = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}
# LOAD DATA
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_POLUSI)
    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df = df.dropna(subset=['tanggal'])
        df['year'] = df['tanggal'].dt.year
        df['month'] = df['tanggal'].dt.month
        df['day'] = df['tanggal'].dt.day
        df['hour'] = df['tanggal'].dt.hour
    return df

try:
    df_mentah = load_data()
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

# SIDEBAR FILTER
st.sidebar.header("Filter")

tahun = st.sidebar.selectbox("Pilih Tahun", sorted(df_mentah['year'].unique()))
df_tahun = df_mentah[df_mentah['year'] == tahun]

bulan_angka_list = sorted(df_tahun['month'].unique())
bulan_nama_list = [NAMA_BULAN[m] for m in bulan_angka_list]
bulan_pilihan = st.sidebar.selectbox("Pilih Bulan", bulan_nama_list)

bulan_angka = [k for k, v in NAMA_BULAN.items() if v == bulan_pilihan][0]
df_bulan = df_tahun[df_tahun['month'] == bulan_angka]

hari_list = sorted(df_bulan['day'].unique())
rentang = st.sidebar.slider("Rentang Hari", min(hari_list), max(hari_list), (min(hari_list), max(hari_list)))

df_filter_tab1 = df_bulan[df_bulan['day'].between(rentang[0], rentang[1])]

# Agregasi Harian
df_harian = df_filter_tab1.groupby(df_filter_tab1['tanggal'].dt.date).mean(numeric_only=True).reset_index()
df_harian.rename(columns={'tanggal': 'date'}, inplace=True)
df_harian['date'] = pd.to_datetime(df_harian['date'])

ambang_batas = {'PM2.5': 55, 'PM10': 75, 'SO2': 75, 'NO2': 65, 'O3': 100, 'CO': 4000}
polutan_tersedia = [p for p in ambang_batas.keys() if p in df_mentah.columns]
warna_map = {'PM2.5': '#0000FF', 'PM10': '#FFA500', 'SO2': '#008000', 'NO2': '#FF0000', 'CO': '#800080', 'O3': '#A52A2A'}


# TAB 1: DASHBOARD HARIAN
with tab1:
    st.markdown(f"### Periode: {rentang[0]}-{rentang[1]} {bulan_pilihan} {tahun}")
    
    cols = st.columns(len(polutan_tersedia))
    rata2 = df_harian[polutan_tersedia].mean()

    for i, polutan in enumerate(polutan_tersedia):
        nilai = rata2[polutan]
        status, warna_delta = ("NORMAL", "normal") if nilai <= ambang_batas[polutan] else ("TINGGI", "inverse")
        cols[i].metric(label=f"{polutan} (µg/m³)", value=f"{nilai:.1f}", delta=status, delta_color=warna_delta)

    st.divider()
    
    col_kiri, col_kanan = st.columns([1, 2])
    with col_kiri:
        st.subheader("Status Kualitas")
        df_harian['Status'] = df_harian[polutan_tersedia].apply(lambda x: "Normal" if (x <= pd.Series(ambang_batas)).all() else "Tidak Sehat", axis=1)
        st.success(f"**{(df_harian['Status'] == 'Normal').sum()} Hari** Normal")
        if (df_harian['Status'] == "Tidak Sehat").any():
            st.error(f"**{(df_harian['Status'] == 'Tidak Sehat').sum()} Hari** Tidak Sehat")

    with col_kanan:
        st.subheader("Tren Fluktuasi Harian")
        option_harian = st.selectbox("Pilih Parameter:", polutan_tersedia, key="sb_harian")
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_alpha(0); ax.patch.set_alpha(0)
        sns.lineplot(data=df_harian, x='date', y=option_harian, marker='o', color="#0064e6", ax=ax)
        ax.axhline(y=ambang_batas[option_harian], color='red', ls='--', alpha=0.7, label='Ambang Batas')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        ax.set_ylabel(f"Konsentrasi {option_harian} (µg/m³)")
        st.pyplot(fig, transparent=True)
        plt.close(fig)

# TAB 2: ANALISIS POLA WAKTU
with tab2:
    st.subheader("Analisis Tren & Pola Waktu")
    
    all_time = st.checkbox("Aktifkan Mode All Time (Gunakan data 2013-2017)", value=True)
    df_pola = df_mentah if all_time else df_filter_tab1
    
    st.info(f"Visualisasi menggunakan: **{'Seluruh Dataset (All Time)' if all_time else 'Data Terfilter Sidebar'}**")
    polutan_pilihan = st.multiselect("Pilih Polutan:", polutan_tersedia, default=polutan_tersedia)
    
    if polutan_pilihan:
        plt.style.use('default')
        st.markdown("### Pola Harian Rata-rata Konsentrasi Polutan")
        n_cols_jam = 3
        n_rows_jam = (len(polutan_pilihan) + n_cols_jam - 1) // n_cols_jam
        
        fig_jam, axes_jam = plt.subplots(n_rows_jam, n_cols_jam, figsize=(18, 5 * n_rows_jam))
        
        axes_jam = axes_jam.flatten()

        for i, polutan in enumerate(polutan_pilihan):
            pola_jam = df_pola.groupby('hour')[polutan].mean()
            jam_puncak = pola_jam.idxmax()
            
            sns.lineplot(x=pola_jam.index, y=pola_jam.values, ax=axes_jam[i], marker='o', color=warna_map.get(polutan, 'blue'))
            axes_jam[i].axvline(x=jam_puncak, color='gray', ls='--', alpha=0.8, label=f'Puncak: Jam {jam_puncak}')
            axes_jam[i].set_title(f"Pola Rata-rata {polutan}", fontsize=12)
            axes_jam[i].set_ylabel(f"Rata-rata {polutan}")
            axes_jam[i].set_xlabel("Pukul")
            axes_jam[i].set_xticks(range(0, 24))
            axes_jam[i].grid(True, alpha=0.2)
            axes_jam[i].legend()

        for j in range(i + 1, len(axes_jam)): fig_jam.delaxes(axes_jam[j])
        plt.tight_layout()
        st.pyplot(fig_jam)

        st.divider()

        st.markdown("### Tren Bulanan Konsentrasi Polutan")
        
        fig_bln, axes_bln = plt.subplots(len(polutan_pilihan), 1, figsize=(15, 3 * len(polutan_pilihan)), sharex=True)
        axes_bln = axes_bln if len(polutan_pilihan) > 1 else [axes_bln]

        df_pola_idx = df_pola.set_index('tanggal').resample('ME').mean(numeric_only=True)

        for i, polutan in enumerate(polutan_pilihan):
            sns.lineplot(data=df_pola_idx, x=df_pola_idx.index, y=polutan, ax=axes_bln[i], color=warna_map.get(polutan, 'blue'))
            axes_bln[i].set_title(f"Tren Bulanan {polutan} (2013-2017)" if all_time else f"Tren {polutan}", loc='left', fontsize=10)
            axes_bln[i].set_ylabel("Konsentrasi")
            axes_bln[i].grid(True, alpha=0.2)
        
        plt.xlabel("Tanggal")
        plt.tight_layout()
        st.pyplot(fig_bln)
    else:
        st.warning("Silakan pilih minimal satu polutan.")
