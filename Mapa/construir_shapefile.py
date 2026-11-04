"""Construye el soporte geográfico de la Entrega 3a.

Lee "Documentación/Entrega 3a Cafeterias y coordenadas.xlsx" (hojas Cafeterias y Zona)
y crea, enlazados por el campo id:
  Mapa/shp/cafeterias.shp        puntos de las cafeterías con coordenadas verificadas
  Mapa/shp/zona_estudio.shp      polígono de la zona de estudio
  Mapa/cafeterias.geojson        los mismos puntos en GeoJSON (se ve directo en GitHub)
  Mapa/mapa_coordenadas.png      mapa simple con las coordenadas reales

Uso, desde la carpeta raíz del repositorio:
  pip install pandas openpyxl geopandas shapely matplotlib
  python Mapa/construir_shapefile.py
"""
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "Documentación" / "Entrega 3a Cafeterias y coordenadas.xlsx"
SALIDA = RAIZ / "Mapa"
COLOR = {"Principal": "#EA4335", "Reserva": "#FBBC04", "Sin encuestas": "#9AA0A6"}

caf = pd.read_excel(BASE, sheet_name="Cafeterias")
zona = pd.read_excel(BASE, sheet_name="Zona")
assert caf["id"].is_unique, "Hay ids repetidos"

faltan = caf.loc[caf["lat"].isna() | caf["lon"].isna(), "id"].tolist()
if faltan:
    print("Sin coordenadas, no entran al mapa:", ", ".join(faltan))
con = caf.dropna(subset=["lat", "lon"]).copy()
if con.empty:
    raise SystemExit("Complete lat y lon en la hoja Cafeterias antes de correr el script.")
fuera = con[~con["lat"].between(4.6, 4.75) | ~con["lon"].between(-74.1, -74.0)]
if not fuera.empty:
    raise SystemExit(f"Coordenadas fuera de la zona norte, revíselas: {fuera['id'].tolist()}")

# Los nombres de campo de un .shp admiten hasta 10 caracteres
campos = {"id": "id", "nombre": "nombre", "direccion": "direccion", "subzona": "subzona",
          "trabajo_campo": "campo", "cumple_regla": "especial", "fuente_coordenada": "fuente_xy"}
pts = gpd.GeoDataFrame(con[list(campos)].rename(columns=campos),
                       geometry=gpd.points_from_xy(con["lon"], con["lat"]), crs="EPSG:4326")
(SALIDA / "shp").mkdir(parents=True, exist_ok=True)
pts.to_file(SALIDA / "shp" / "cafeterias.shp", encoding="utf-8")
pts.to_file(SALIDA / "cafeterias.geojson", driver="GeoJSON")

pol = None
if zona[["lat", "lon"]].notna().all().all():
    pol = gpd.GeoDataFrame({"zona": ["Chicó, Parque 93 y Zona T"]},
                           geometry=[Polygon(zip(zona["lon"], zona["lat"]))], crs="EPSG:4326")
    pol.to_file(SALIDA / "shp" / "zona_estudio.shp", encoding="utf-8")
else:
    print("Faltan coordenadas en la hoja Zona: no se crea el polígono.")

fig, ax = plt.subplots(figsize=(7, 9))
if pol is not None:
    pol.plot(ax=ax, color="#e8f5e9", edgecolor="#0f8c6c")
for estado, color in COLOR.items():
    sub = pts[pts["campo"] == estado]
    if not sub.empty:
        sub.plot(ax=ax, color=color, markersize=70, edgecolor="white", label=estado)
for _, r in pts.iterrows():
    ax.annotate(f'{r["id"]} {r["nombre"]}', (r.geometry.x, r.geometry.y), xytext=(5, 3),
                textcoords="offset points", fontsize=8)
ax.set_title("Cafeterías de especialidad: Chicó, Parque 93 y Zona T\nCoordenadas verificadas en Google Maps (EPSG:4326)", fontsize=10)
ax.set_xlabel("Longitud"); ax.set_ylabel("Latitud"); ax.legend(fontsize=8, frameon=False)
fig.savefig(SALIDA / "mapa_coordenadas.png", dpi=200, bbox_inches="tight")
print(f"Listo: {len(pts)} cafeterías en Mapa/shp/cafeterias.shp y Mapa/cafeterias.geojson")
