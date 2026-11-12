"""
Entrega 5 - Gráficos de la encuesta.

Entrada:  Datos/clean/encuestas_clean.csv  (sale de Scripts/01_limpieza.py)
Salida:   Graficos/*.png  (un archivo por gráfico)

Cómo correrlo (desde la carpeta del repositorio):
  pip install pandas matplotlib
  python Scripts/02_graficos.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

RAIZ = Path(__file__).resolve().parents[1]
df = pd.read_csv(RAIZ / "Datos" / "clean" / "encuestas_clean.csv")
SALIDA = RAIZ / "Graficos"
SALIDA.mkdir(exist_ok=True)

GRUPOS = ["Jóvenes (18-29)", "Adultos (30-45)", "Mayores (46+)"]
COLOR = {"Jóvenes (18-29)": "#E69F00", "Adultos (30-45)": "#009E73", "Mayores (46+)": "#0072B2"}
FUENTE = f"Fuente: encuesta propia en 6 cafeterías de especialidad de la zona norte de Bogotá, oct.-nov. 2026 (n = {len(df)})."
df["grupo_edad"] = pd.Categorical(df["grupo_edad"], GRUPOS, ordered=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10.5, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#888888", "axes.labelcolor": "#333333",
    "xtick.color": "#444444", "ytick.color": "#444444",
    "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
})
pesos = FuncFormatter(lambda x, _: f"${x:,.0f}".replace(",", "."))
rng = np.random.default_rng(2026)


def guardar(fig, nombre, nota=FUENTE, y=-0.02):
    fig.text(0.01, y, nota, fontsize=8, color="#666666", ha="left", va="top")
    fig.savefig(SALIDA / nombre)
    plt.close(fig)
    print("  ", nombre)


def caja_por_grupo(col, titulo, eje, nombre, formato=None, datos=None, nota=FUENTE, log=False):
    """Caja (cuartiles) + puntos individuales + mediana escrita, por grupo de edad."""
    d = (df if datos is None else datos).dropna(subset=[col])
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for i, g in enumerate(GRUPOS):
        v = d.loc[d.grupo_edad == g, col]
        ax.boxplot(v, positions=[i], widths=0.5, showfliers=False, patch_artist=True,
                   boxprops=dict(facecolor=COLOR[g] + "33", edgecolor=COLOR[g], linewidth=1.5),
                   medianprops=dict(color=COLOR[g], linewidth=2.5),
                   whiskerprops=dict(color=COLOR[g]), capprops=dict(color=COLOR[g]))
        ax.scatter(i + rng.uniform(-0.17, 0.17, len(v)), v, s=14, color=COLOR[g], alpha=0.55,
                   edgecolor="none", zorder=3)
        med = v.median()
        texto = formato(med) if formato else f"{med:g}"
        ax.annotate(f"Mediana: {texto}", (i + 0.3, med), fontsize=9, color="#222222",
                    va="center", ha="left", fontweight="bold")
    ax.set_xticks(range(3), [f"{g}\nn = {(d.grupo_edad == g).sum()}" for g in GRUPOS])
    ax.set_xlim(-0.6, 2.95)
    if log:
        ax.set_yscale("log")
    if formato:
        ax.yaxis.set_major_formatter(pesos)
    ax.set_ylabel(eje)
    ax.set_title(titulo)
    ax.grid(axis="y", color="#e5e5e5")
    ax.set_axisbelow(True)
    guardar(fig, nombre, nota)


def barras_100(col, orden, titulo, nombre, nota=FUENTE):
    """Barras horizontales al 100 %: composición de cada grupo de edad."""
    tab = pd.crosstab(df.grupo_edad, df[col], normalize="index")[orden].reindex(GRUPOS)
    paleta = ["#0072B2", "#56B4E9", "#009E73", "#E69F00", "#D55E00", "#CC79A7", "#999999"]
    fig, ax = plt.subplots(figsize=(9, 3.9))
    izq = np.zeros(len(GRUPOS))
    for k, cat in enumerate(orden):
        val = tab[cat].values
        ax.barh(GRUPOS, val, left=izq, color=paleta[k], label=cat, edgecolor="white", height=0.62)
        for y, (x0, w) in enumerate(zip(izq, val)):
            if w >= 0.07:
                ax.text(x0 + w / 2, y, f"{w:.0%}", ha="center", va="center", fontsize=9,
                        color="white", fontweight="bold")
        izq += val
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlim(0, 1)
    ax.legend(ncol=min(len(orden), 3), loc="upper left", bbox_to_anchor=(0, -0.1), frameon=False, fontsize=9)
    ax.set_title(titulo)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    guardar(fig, nombre, nota, y=-0.2)


print("Generando gráficos en", SALIDA)

# 1. Muestra por rango de edad --------------------------------------------------------
orden_edad = ["18 a 24", "25 a 29", "30 a 37", "38 a 45", "46 a 55", "56 o más"]
grupo_de = {"18 a 24": GRUPOS[0], "25 a 29": GRUPOS[0], "30 a 37": GRUPOS[1],
            "38 a 45": GRUPOS[1], "46 a 55": GRUPOS[2], "56 o más": GRUPOS[2]}
n = df.p12_edad.value_counts().reindex(orden_edad)
fig, ax = plt.subplots(figsize=(8, 4.2))
barras = ax.bar(orden_edad, n.values, color=[COLOR[grupo_de[e]] for e in orden_edad], width=0.65)
ax.bar_label(barras, padding=3, fontsize=10, fontweight="bold")
for g in GRUPOS:
    ax.bar(0, 0, color=COLOR[g], label=f"{g}: {(df.grupo_edad == g).sum()}")
ax.legend(frameon=False, loc="upper center", ncol=3, fontsize=9)
ax.set_ylabel("Encuestas válidas")
ax.set_xlabel("Rango de edad")
ax.set_title("Encuestas válidas por rango de edad")
ax.set_ylim(0, n.max() * 1.35)
guardar(fig, "01_muestra_por_edad.png")

# 2. Frecuencia: visitas en los últimos 30 días ------------------------------------
caja_por_grupo("p6_visitas_30d", "Visitas a cafeterías de especialidad en los últimos 30 días",
               "Visitas en 30 días (contando la de hoy)", "02_visitas_30d.png")

# 3. Gasto por visita (solo quienes pagaron únicamente lo suyo) --------------------
propio = df[df.p5_tipo_pago == "Solo lo mío"]
caja_por_grupo("gasto_visita_propio", "Gasto en esta visita, pagando solo lo propio",
               "Pesos pagados en la visita", "03_gasto_visita.png",
               formato=lambda x: f"${x:,.0f}".replace(",", "."), datos=propio,
               nota=FUENTE.replace(f"(n = {len(df)}).", f"(n = {len(propio)}).\nSe excluyen las cuentas compartidas y las pagadas por otra persona."))

# 4. Gasto en 30 días ----------------------------------------------------------------
caja_por_grupo("p7_gasto_30d", "Gasto en cafeterías de especialidad en los últimos 30 días",
               "Pesos en 30 días (escala logarítmica)", "04_gasto_30d.png",
               formato=lambda x: f"${x:,.0f}".replace(",", "."), log=True)

# 5. Disposición a pagar --------------------------------------------------------------
caja_por_grupo("p10_dap", "Máximo que pagaría por un americano de especialidad de 8 oz",
               "Pesos", "05_disposicion_a_pagar.png",
               formato=lambda x: f"${x:,.0f}".replace(",", "."))

# 6. Motivo principal -----------------------------------------------------------------
barras_100("p1_motivo", ["Socializar", "Estudiar o trabajar", "Disfrutar un buen café",
                         "De paso o por practicidad", "Reunión de trabajo", "Otro"],
           "Motivo principal de la visita por grupo de edad", "06_motivo.png")

# 7. Importancia de los atributos (P11) ----------------------------------------------
atrib = {"p11a_calidad": "Calidad del café", "p11b_barista": "Barista", "p11c_ambiente": "Ambiente y estética",
         "p11d_wifi": "WiFi y enchufes", "p11e_espacio": "Espacio para quedarse",
         "p11f_tranquilidad": "Tranquilidad", "p11g_precio": "Precio", "p11h_cercania": "Cercanía"}
medias = df.groupby("grupo_edad", observed=True)[list(atrib)].mean().T.rename(index=atrib)
medias = medias.loc[medias.mean(axis=1).sort_values().index]
fig, ax = plt.subplots(figsize=(8.5, 5))
y = np.arange(len(medias))
ax.hlines(y, medias.min(axis=1), medias.max(axis=1), color="#cccccc", linewidth=3, zorder=1)
for k, g in enumerate(GRUPOS):
    ax.scatter(medias[g], y, s=70, color=COLOR[g], label=g, zorder=3, edgecolor="white")
ax.set_yticks(y, medias.index)
ax.set_xlim(1, 5)
ax.set_xlabel("Importancia promedio (1 = nada importante, 5 = muy importante)")
ax.set_title("Importancia de los atributos de la cafetería por grupo de edad")
ax.legend(frameon=False, loc="lower right")
ax.grid(axis="x", color="#e5e5e5")
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
guardar(fig, "07_atributos.png")

# 8. Permanencia ------------------------------------------------------------------------
barras_100("p3_permanencia", ["Para llevar", "Menos de 30 min", "30 a 60 min", "1 a 2 horas", "Más de 2 horas"],
           "Tiempo que piensa quedarse en la cafetería", "08_permanencia.png")

# 9. Con quién vino --------------------------------------------------------------------
barras_100("p2_compania", ["Solo", "Amigos", "Pareja o familia", "Compañeros de trabajo o estudio"],
           "Con quién vino a la cafetería", "09_compania.png")

# 10. Frecuencia frente a gasto por visita -------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
for g in GRUPOS:
    d = df[df.grupo_edad == g]
    ax.scatter(d.p6_visitas_30d + rng.uniform(-0.25, 0.25, len(d)), d.gasto_por_visita_30d,
               s=26, alpha=0.7, color=COLOR[g], label=g, edgecolor="white", linewidth=0.4)
ax.set_xlabel("Visitas en los últimos 30 días")
ax.set_ylabel("Gasto promedio por visita en el mes (P7 / P6)")
ax.yaxis.set_major_formatter(pesos)
ax.set_title("Frecuencia de visita frente a gasto promedio por visita")
ax.legend(frameon=False)
ax.grid(color="#eeeeee")
ax.set_axisbelow(True)
guardar(fig, "10_frecuencia_vs_gasto.png")

print("Listo.")
