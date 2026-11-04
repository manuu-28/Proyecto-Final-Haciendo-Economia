"""Entrega 4: genera las tablas y la figura del informe de trabajo de campo.

Lee:
  Documentación/Entrega 3b Base encuestas.xlsx      (hojas Datos y Bitacora)
  Documentación/Entrega 3a Cafeterias y coordenadas.xlsx (hoja Cafeterias)
Escribe en Documentación/Entrega 4/:
  tablas_campo.tex   tablas y cifras que el informe incluye con \\input
  figura_cuotas.png  encuestas por grupo de edad frente a la meta

Uso, desde la carpeta raíz del repositorio:
  pip install pandas openpyxl matplotlib
  python Scripts/informe_campo.py
Después compile "Documentación/Entrega 4/Entrega 4 Informe trabajo de campo.tex".
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "Documentación"
SAL = DOC / "Entrega 4"
FRANJAS = ["Mañana laboral", "Mediodía laboral", "Tarde laboral", "Sábado"]
PRINCIPALES = ["C01", "C02", "C03", "C05", "C07", "C08"]
GRUPOS = {"Jóvenes (18 a 29)": ["18 a 24", "25 a 29"],
          "Adultos (30 a 45)": ["30 a 37", "38 a 45"],
          "Mayores (46 o más)": ["46 a 55", "56 o más"]}
META_SESION, META_GRUPO = 7, 56


def tex(x):
    """Escapa caracteres especiales de LaTeX en textos que vienen de la base."""
    s = "" if pd.isna(x) else str(x)
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}")]:
        s = s.replace(a, b)
    return s


def pct(a, b):
    return f"{100 * a / b:.0f}\\%" if b else "--"


datos = pd.read_excel(DOC / "Entrega 3b Base encuestas.xlsx", sheet_name="Datos")
datos = datos[datos["id_encuesta"].notna() & (datos["id_encuesta"] != "EJEMPLO")]
bit = pd.read_excel(DOC / "Entrega 3b Base encuestas.xlsx", sheet_name="Bitacora")
bit = bit[bit["fecha"].notna() & ~bit["incidentes"].astype(str).str.startswith("Fila de ejemplo")]
caf = pd.read_excel(DOC / "Entrega 3a Cafeterias y coordenadas.xlsx", sheet_name="Cafeterias")
nombres = dict(zip(caf["id"], caf["nombre"]))

validas = datos[(datos["consentimiento"] == "Sí") & (datos["mayor_18"] == "Sí")].copy()
grupo_de = {r: g for g, rs in GRUPOS.items() for r in rs}
validas["grupo"] = validas["p12_edad"].map(grupo_de)

L = []
m = lambda nombre, valor: L.append(f"\\newcommand{{\\{nombre}}}{{{valor}}}")
n_abord, n_val = len(datos), len(validas)
m("nabordadas", n_abord); m("nvalidas", n_val); m("tasarespuesta", pct(n_val, n_abord))
m("nsesiones", int((bit["permiso"] == "Sí").sum())); m("nsinpermiso", int((bit["permiso"] == "No").sum()))
m("nextra", int((bit["sesion_extra"] == "Sí").sum()))
m("fechainicio", tex(bit["fecha"].min()) if len(bit) else "--")
m("fechafin", tex(bit["fecha"].max()) if len(bit) else "--")

# Tabla 1: encuestas válidas por cafetería y franja frente a la meta de 7
L.append(r"\newcommand{\tablasesiones}{\begin{tabular}{@{}l" + "c" * len(FRANJAS) + r"c@{}}\toprule")
L.append("Cafetería & " + " & ".join(FRANJAS) + r" & Total \\ \midrule")
usadas = PRINCIPALES + [c for c in validas["id_cafeteria"].dropna().unique() if c not in PRINCIPALES]
for c in usadas:
    sub = validas[validas["id_cafeteria"] == c]
    celdas = [f"{(sub['franja'] == f).sum()}/{META_SESION}" for f in FRANJAS]
    etiqueta = f"{c} {tex(nombres.get(c, ''))}" + ("" if c in PRINCIPALES else " (reserva)")
    L.append(f"{etiqueta} & " + " & ".join(celdas) + f" & {len(sub)} \\\\")
L.append(r"\midrule Total & " + " & ".join(str((validas['franja'] == f).sum()) for f in FRANJAS)
         + f" & {n_val} \\\\ \\bottomrule\\end{{tabular}}}}")

# Tabla 2: cuotas por grupo de edad
L.append(r"\newcommand{\tablagrupos}{\begin{tabular}{@{}lccc@{}}\toprule Grupo de edad & Encuestas & Meta & Cumplimiento \\ \midrule")
conteo = {}
for g in GRUPOS:
    k = int((validas["grupo"] == g).sum()); conteo[g] = k
    L.append(f"{g} & {k} & {META_GRUPO} & {pct(k, META_GRUPO)} \\\\")
sin_edad = int(validas["grupo"].isna().sum())
if sin_edad:
    L.append(f"Sin rango de edad & {sin_edad} & -- & -- \\\\")
L.append(f"\\midrule Total & {n_val} & {META_GRUPO * 3} & {pct(n_val, META_GRUPO * 3)} \\\\ \\bottomrule\\end{{tabular}}}}")

# Tabla 3: participación
L.append(r"\newcommand{\tablaparticipacion}{\begin{tabular}{@{}lc@{}}\toprule Resultado & Personas \\ \midrule")
L.append(f"Encuestas completas & {n_val} \\\\")
for rz in ["No acepta", "Menor de edad", "Se retiró a mitad"]:
    L.append(f"{rz} & {int((datos['razon_no_participa'] == rz).sum())} \\\\")
L.append(f"\\midrule Personas abordadas & {n_abord} \\\\ Tasa de respuesta & {pct(n_val, n_abord)} \\\\ \\bottomrule\\end{{tabular}}}}")

# Tabla 4: preguntas sin respuesta por grupo de edad
claves = [("p5_pago_visita", "Gasto de la visita (P5)"), ("p6_visitas_30d", "Visitas en 30 días (P6)"),
          ("p7_gasto_30d", "Gasto en 30 días (P7)"), ("p10_dap", "Disposición a pagar (P10)"),
          ("p14_estrato", "Estrato (P14)")]
L.append(r"\newcommand{\tablanorespuesta}{\begin{tabular}{@{}l" + "c" * len(GRUPOS) + r"@{}}\toprule Variable & "
         + " & ".join(g.split(" (")[0] for g in GRUPOS) + r" \\ \midrule")
for col, lab in claves:
    fila = []
    for g in GRUPOS:
        sub = validas[validas["grupo"] == g]
        falta = sub[col].isna() | (sub[col].astype(str) == "Prefiero no responder")
        fila.append(pct(int(falta.sum()), len(sub)))
    L.append(f"{lab} & " + " & ".join(fila) + r" \\")
L.append(r"\bottomrule\end{tabular}}")

# Tabla 5: verificación de la regla de especialidad en la visita
def regla(r):
    c = [r["c1_origen"], r["c2_metodos"], r["c3_tostion"], r["c4_reconocimiento"]]
    if c[0] == "No":
        return "No"
    if c[0] == "Sí" and "Sí" in c[1:]:
        return "Sí"
    return "Por verificar"
L.append(r"\newcommand{\tablaregla}{\begin{tabular}{@{}llccc@{}}\toprule id & Cafetería & Campo & Verificada en visita & Cumple la regla \\ \midrule")
for _, r in caf.iterrows():
    L.append(f"{r['id']} & {tex(r['nombre'])} & {tex(r['trabajo_campo'])} & {tex(r['verificado_en_visita'])} {tex(r['fecha_visita'])} & {regla(r)} \\\\")
L.append(r"\bottomrule\end{tabular}}")

# Incidentes, reemplazos y sesiones sin permiso registrados en la bitácora
inc = [f"\\item {tex(r['fecha'])}, {r['id_cafeteria']}, {tex(r['franja'])}: {tex(r['incidentes'])}"
       for _, r in bit.iterrows() if pd.notna(r["incidentes"]) and str(r["incidentes"]).strip()]
rem = [f"\\item {r['id_cafeteria']} reemplazó a {tex(r['reemplaza_a'])} ({tex(r['franja'])}, {tex(r['fecha'])})"
       for _, r in bit.iterrows() if pd.notna(r["reemplaza_a"]) and str(r["reemplaza_a"]).strip()]
L.append(r"\newcommand{\listaincidentes}{" + (r"\begin{itemize}" + "".join(inc) + r"\end{itemize}" if inc else "No se registraron incidentes en la bitácora.") + "}")
L.append(r"\newcommand{\listareemplazos}{" + (r"\begin{itemize}" + "".join(rem) + r"\end{itemize}" if rem else "No hubo reemplazos de cafeterías.") + "}")

SAL.mkdir(parents=True, exist_ok=True)
(SAL / "tablas_campo.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

fig, ax = plt.subplots(figsize=(6, 3.2))
ax.bar([g.split(" (")[0] for g in GRUPOS], list(conteo.values()), color="#0f8c6c")
ax.axhline(META_GRUPO, color="#EA4335", ls="--", lw=1.2, label=f"Meta: {META_GRUPO}")
for i, v in enumerate(conteo.values()):
    ax.text(i, v + 0.8, str(v), ha="center", fontsize=9)
ax.set_ylabel("Encuestas válidas"); ax.legend(frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(SAL / "figura_cuotas.png", dpi=200)
print(f"Listo: {n_val} encuestas válidas de {n_abord} personas abordadas. Tablas en {SAL / 'tablas_campo.tex'}")
