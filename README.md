# 🌫️ Dashboard Air Quality Changping

Dashboard interaktif untuk memantau dan menganalisis kualitas udara di distrik Changping pada periode 2013 hingga 2017. Dashboard dibangun menggunakan Streamlit.

✨ Fitur

- **Ringkasan Harian**: menampilkan rata-rata konsentrasi polutan pada periode terpilih, status kualitas udara (Normal atau Tidak Sehat), serta tren fluktuasi harian.
- **Analisis Pola Waktu**: menampilkan pola rata-rata per jam dan tren bulanan untuk setiap polutan (PM2.5, PM10, SO2, NO2, CO, dan O3).
- **Filter Interaktif**: pengguna dapat memilih tahun, bulan, dan rentang hari, atau mengaktifkan mode All Time untuk menganalisis seluruh data tahun 2013 hingga 2017.

📁 Struktur Folder

```text
dashboard/
├── dashboard.py       # Kode utama dashboard Streamlit
├── data_polusi.csv    # Dataset polusi Changping 2013-2017
├── requirements.txt   # Daftar dependensi
└── link.txt           # Tautan deployment Streamlit Cloud
```

🚀 Cara Menjalankan di Lokal

### 1. Memastikan Kelengkapan File

Pastikan seluruh file pada struktur folder di atas telah tersedia.

### 2. Membuka Folder Dashboard

```bash
cd lokasi/folder/dashboard
```

### 3. Membuat dan Mengaktifkan Virtual Environment

```bash
python -m venv venv
```

Aktifkan virtual environment sesuai sistem operasi yang digunakan:

| Sistem Operasi | Perintah |
|----------------|----------|
| Windows | `venv\Scripts\activate` |
| macOS dan Linux | `source venv/bin/activate` |

### 4. Menginstal Dependensi

```bash
pip install -r requirements.txt
```

### 5. Menjalankan Dashboard

```bash
streamlit run dashboard.py
```

Setelah perintah dijalankan, dashboard akan terbuka di browser, umumnya pada alamat `http://localhost:8501`.

☁️ Deployment

Dashboard ini telah ter-deploy menggunakan Streamlit Community Cloud. Tautan deployment tersedia pada berkas `link.txt`.
