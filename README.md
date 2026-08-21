# 🪐 Exoplanet Confirmation & Habitability Analysis Dashboard

An interactive astrophysics and data science web application built with **Streamlit** and **Plotly 3D**. It queries live candidate data from the **NASA Exoplanet Archive TAP API** (Kepler, TESS TOI, and K2), computes habitable zone boundaries, scores candidates using planetary science models, and renders interactive 3D orbital animations.

---

## 🌟 Key Features

- **Multi-Mission NASA Data Pipeline**: Programmatic SQL access via Table Access Protocol (TAP) to unconfirmed candidates from Kepler, TESS (TOI), and K2.
- **Astrophysics & Habitability Engine**:
  - **Kopparapu et al. (2013)** Habitable Zone (Conservative & Optimistic boundaries)
  - **Earth Similarity Index (ESI)**
  - **Tidal Locking Estimation** for M-dwarf host stars
  - **Composite Habitability Scoring**
- **3D Orbital Simulation**: Custom Plotly 3D Keplerian orbital mechanics renderer with star temperature color grading, habitable zone rings, and orbit tracks.
- **Interactive Multi-Page UI**:
  - 🏠 **Dashboard**: High-level candidate statistics & top habitable worlds
  - 🔎 **Candidate Explorer**: Multi-variable filters, sorting, and CSV export
  - 🌌 **3D System Viewer**: Orbit visualizer for any candidate system
  - 📈 **Population Analytics**: Statistical charts, radius gap, and mission comparison

---

## 🚀 Getting Started

### 1. Clone or Navigate to the Repository
```bash
git clone https://github.com/YOUR_USERNAME/exoplanet-dashboard.git
cd exoplanet-dashboard
```

### 2. Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt pyarrow
```

### 4. Run the Dashboard
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
exoplanet-dashboard/
├── app.py                  # Main application & routing
├── config.py               # Constants, HZ coefficients & styling maps
├── requirements.txt        # Python package dependencies
├── test_backend.py         # Verification test suite
│
├── data/
│   ├── fetcher.py          # NASA TAP API fetcher & parquet local caching
│   └── cache/              # Cached data
│
├── science/
│   ├── habitability.py     # HZ boundary equations, ESI & scoring models
│   └── orbital.py          # Kepler equation solver & 3D coordinate transforms
│
├── pages/
│   ├── dashboard.py        # Dashboard view
│   ├── explorer.py         # Explorer table & filters
│   ├── system_viewer.py    # 3D orbital viewer
│   └── analytics.py        # Deep dive charts
│
├── components/
│   ├── cards.py            # UI cards & badges
│   ├── filters.py          # Sidebar search widgets
│   └── plots.py            # Dark space themed Plotly figures
│
└── assets/
    └── style.css           # Custom CSS styling
```

---

## 🔬 Scientific References

- Kopparapu, R. K. et al. (2013). *Habitable Zones around Main-Sequence Stars: New Estimates.* The Astrophysical Journal, 765(2), 131.
- Schulze-Makuch, D. et al. (2011). *A Two-Tiered Approach to Assessing the Habitability of Exoplanets.* Astrobiology, 11(10), 1041-1052.
- Chen, J., & Kipping, D. (2017). *Probabilistic Forecasting of the Masses and Radii of Other Worlds.* The Astrophysical Journal, 834(1), 17.
- NASA Exoplanet Archive (IPAC/Caltech).
