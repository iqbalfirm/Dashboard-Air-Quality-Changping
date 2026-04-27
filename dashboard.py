import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

st.set_page_config(page_title="Dashboard Kualitas Udara Changping", layout="wide")

#Header
st.title("Dashboard Kualitas Udara Changping")
tab1, tab2 = st.tabs(["Ringkasan Harian", "Analisis Pola Waktu"])

#Konfigurasi
DATA_POLUSI = "data_polusi.csv"

NAMA_BULAN = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

ambang_batas = {'PM2.5': 55, 'PM10': 75, 'SO2': 75, 'NO2': 65, 'O3': 100, 'CO': 4000}
warna_map = {'PM2.5': '#0000FF', 'PM10': '#FFA500', 'SO2': '#008000', 'NO2': '#FF0000', 'CO': '#800080', 'O3': '#A52A2A'}

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_POLUSI)

    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
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

# Sidebar
st.sidebar.header("Filter")

tahun = st.sidebar.selectbox("Pilih Tahun", sorted(df_mentah['year'].unique()))
df_tahun = df_mentah[df_mentah['year'] == tahun]

bulan_angka_list = sorted(df_tahun['month'].unique())
bulan_nama_list = [NAMA_BULAN[m] for m in bulan_angka_list]

if not bulan_nama_list:
    st.warning("Data tidak tersedia.")
    st.stop()

bulan_pilihan = st.sidebar.selectbox("Pilih Bulan", bulan_nama_list)
bulan_angka = [k for k, v in NAMA_BULAN.items() if v == bulan_pilihan][0]

df_bulan = df_tahun[df_tahun['month'] == bulan_angka]

hari_list = sorted(df_bulan['day'].unique())
rentang = st.sidebar.slider(
    "Rentang Hari",
    min(hari_list), max(hari_list),
    (min(hari_list), max(hari_list))
)

df_filter = df_bulan[df_bulan['day'].between(rentang[0], rentang[1])]

polutan_tersedia = [p for p in ambang_batas.keys() if p in df_filter.columns]

df_harian = (
    df_filter
    .groupby(df_filter['tanggal'].dt.date)
    .mean(numeric_only=True)
    .reset_index()
)

df_harian.rename(columns={'tanggal': 'date'}, inplace=True)
df_harian['date'] = pd.to_datetime(df_harian['date'])

# TAB 1 Analisis Harian
with tab1:
    st.markdown(f"### Periode: {rentang[0]}-{rentang[1]} {bulan_pilihan} {tahun}")

    if df_harian.empty:
        st.warning("Data harian tidak tersedia.")
    else:
        cols = st.columns(len(polutan_tersedia))
        rata2 = df_harian[polutan_tersedia].mean()

        for i, polutan in enumerate(polutan_tersedia):
            nilai = rata2[polutan]
            status = "NORMAL" if nilai <= ambang_batas[polutan] else "TINGGI"

            cols[i].metric(
                label=f"{polutan} (µg/m³)",
                value=f"{nilai:.1f}",
                delta=status,
                delta_color="normal" if status == "NORMAL" else "inverse"
            )
        st.divider()
        col_kiri, col_kanan = st.columns([1, 2])

        with col_kiri:
            st.subheader("Status Kualitas")

            df_harian['Status'] = df_harian[polutan_tersedia].apply(
                lambda x: "Normal" if (x <= pd.Series(ambang_batas)).all() else "Tidak Sehat",
                axis=1
            )

            st.success(f"{(df_harian['Status'] == 'Normal').sum()} Hari Normal")

            if (df_harian['Status'] == "Tidak Sehat").any():
                st.error(f"{(df_harian['Status'] == 'Tidak Sehat').sum()} Hari Tidak Sehat")

        with col_kanan:
            st.subheader("Tren Fluktuasi Harian")

            option_harian = st.selectbox("Pilih Parameter:", polutan_tersedia, key="sb_harian")

            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_alpha(0); ax.patch.set_alpha(0)

            sns.lineplot(data=df_harian, x='date', y=option_harian, marker='o', color="#0064e6", ax=ax)

            ax.axhline(y=ambang_batas[option_harian], color='red', ls='--', alpha=0.7)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))

            st.pyplot(fig, transparent=True)
            plt.close(fig)

# TAB 2 Analisis Tren 
with tab2:
    st.subheader("Analisis Tren & Pola Waktu")

    all_time = st.checkbox("Aktifkan Mode All Time (Gunakan data 2013-2017)", value=True)

    if all_time:
        df_pola = df_mentah
        st.warning("Mode All Time aktif — filter sidebar (tahun, bulan, hari) tidak digunakan.")
    else:
        df_pola = df_filter
        st.info(f"Menampilkan data: {bulan_pilihan} {tahun}")

    if df_pola.empty:
        st.warning("Data tidak tersedia.")
    else:
        polutan_pilihan = st.multiselect("Pilih Polutan:", polutan_tersedia, default=polutan_tersedia)

        if polutan_pilihan:
            st.markdown("### Pola Harian Rata-rata")

            n_cols = 3
            n_rows = (len(polutan_pilihan) + n_cols - 1) // n_cols

            fig_jam, axes_jam = plt.subplots(n_rows, n_cols, figsize=(18, 5 * n_rows))
            axes_jam = axes_jam.flatten() if hasattr(axes_jam, 'flatten') else [axes_jam]

            for i, polutan in enumerate(polutan_pilihan):
                pola_jam = df_pola.groupby('hour')[polutan].mean()

                # ambil jam puncak
                jam_puncak = pola_jam.idxmax()

                sns.lineplot(
                    x=pola_jam.index,
                    y=pola_jam.values,
                    ax=axes_jam[i],
                    marker='o',
                    color=warna_map.get(polutan, 'blue')
                )
                axes_jam[i].axvline(
                    x=jam_puncak,
                    linestyle='--',
                    color='gray',
                    alpha=0.8
                )

                axes_jam[i].set_title(f"Pola Jam {polutan}")
                axes_jam[i].set_xticks(range(0, 24))
                axes_jam[i].grid(True, alpha=0.2)

            for j in range(i + 1, len(axes_jam)):
                fig_jam.delaxes(axes_jam[j])

            plt.tight_layout()
            st.pyplot(fig_jam)

            st.markdown("### Tren Bulanan")

            df_resample = df_pola.set_index('tanggal')
            df_tren_bulan = df_resample.resample('ME').mean(numeric_only=True)

            if not df_tren_bulan.empty:
                fig_bln, axes_bln = plt.subplots(
                    len(polutan_pilihan),
                    1,
                    figsize=(15, 3 * len(polutan_pilihan)),
                    sharex=True
                )

                axes_bln = axes_bln if len(polutan_pilihan) > 1 else [axes_bln]

                for i, polutan in enumerate(polutan_pilihan):
                    sns.lineplot(
                        data=df_tren_bulan,
                        x=df_tren_bulan.index,
                        y=polutan,
                        ax=axes_bln[i],
                        color=warna_map.get(polutan, 'blue')
                    )

                    axes_bln[i].set_title(f"Tren {polutan}", loc='left')
                    axes_bln[i].grid(True, alpha=0.2)

                plt.tight_layout()
                st.pyplot(fig_bln)
            else:
                st.warning("Data tidak cukup untuk menampilkan tren bulanan.")
