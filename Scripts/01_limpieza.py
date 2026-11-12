"""
Entrega 5 - Limpieza de datos.

Entrada (raw, no se modifica):
  Datos/raw/encuestas_raw.xlsx   hojas Datos (una fila por persona abordada) y Cafeterias

Salidas (clean/tidy):
  Datos/clean/encuestas_clean.csv   168 encuestas válidas, una fila por persona
  Datos/clean/encuestas_clean.xlsx  lo mismo en Excel, con la hoja Diccionario
  Datos/clean/abordajes.csv         las 233 personas abordadas, para la tasa de respuesta
  Datos/clean/resumen_por_grupo.csv medianas y medias por grupo de edad

Cómo correrlo (desde la carpeta del repositorio):
  pip install pandas openpyxl
  python Scripts/01_limpieza.py
"""
import warnings
from pathlib import Path
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "Datos" / "raw" / "encuestas_raw.xlsx"
CLEAN = RAIZ / "Datos" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)

datos = pd.read_excel(RAW, sheet_name="Datos", dtype=str)
cafes = pd.read_excel(RAW, sheet_name="Cafeterias", dtype=str)[["id", "nombre", "subzona"]]
datos = datos.apply(lambda s: s.str.strip())          # quita espacios sobrantes
datos = datos.replace({"": pd.NA})
print(f"Personas abordadas (raw): {len(datos)}")

# 1. Abordajes: todas las personas, con indicador de encuesta válida ---------------
abordajes = datos[["id_encuesta", "id_cafeteria", "fecha", "franja", "encuestador",
                   "consentimiento", "mayor_18", "razon_no_participa"]].copy()
abordajes["valida"] = ((abordajes.consentimiento == "Sí") & (abordajes.mayor_18 == "Sí")).astype(int)
abordajes["fecha"] = pd.to_datetime(abordajes["fecha"]).dt.date
abordajes.to_csv(CLEAN / "abordajes.csv", index=False, encoding="utf-8-sig")

# 2. Encuestas válidas --------------------------------------------------------------
df = datos[(datos.consentimiento == "Sí") & (datos.mayor_18 == "Sí")].copy()
df = df.drop(columns=["consentimiento", "mayor_18", "razon_no_participa"])
print(f"Encuestas válidas: {len(df)}")

# Tipos: fechas y números
df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
numericas = ["p5_pago_visita", "p6_visitas_30d", "p7_gasto_30d", "p8_visitas_zona",
             "p9_tazas_dia", "p10_dap"]
for c in numericas:
    df[c] = pd.to_numeric(df[c], errors="raise")
escalas = [c for c in df.columns if c.startswith("p11")]
for c in escalas:
    df[c] = pd.to_numeric(df[c], errors="raise").astype("Int64")

# Sí/No de la pregunta 4 y la compra pendiente -> 1/0
for c in ["p4_cafe", "p4_otra_bebida", "p4_comida", "p4_grano", "p5_compra_pendiente"]:
    df[c] = df[c].map({"Sí": 1, "No": 0}).astype("Int64")

# Estrato: "Prefiero no responder" pasa a dato faltante
df["p14_estrato"] = pd.to_numeric(df["p14_estrato"].replace("Prefiero no responder", pd.NA)).astype("Int64")

# 3. Variables nuevas ---------------------------------------------------------------
orden_edad = ["18 a 24", "25 a 29", "30 a 37", "38 a 45", "46 a 55", "56 o más"]
grupo = {"18 a 24": "Jóvenes (18-29)", "25 a 29": "Jóvenes (18-29)",
         "30 a 37": "Adultos (30-45)", "38 a 45": "Adultos (30-45)",
         "46 a 55": "Mayores (46+)", "56 o más": "Mayores (46+)"}
df["grupo_edad"] = df["p12_edad"].map(grupo)
df["p12_edad"] = pd.Categorical(df["p12_edad"], categories=orden_edad, ordered=True)
df["grupo_edad"] = pd.Categorical(df["grupo_edad"],
                                  categories=["Jóvenes (18-29)", "Adultos (30-45)", "Mayores (46+)"],
                                  ordered=True)

# Gasto propio de la visita: solo cuando el monto es únicamente lo de la persona
df["gasto_visita_propio"] = df["p5_pago_visita"].where(df["p5_tipo_pago"] == "Solo lo mío")
# Gasto promedio por visita en el mes y peso de la zona en las visitas
df["gasto_por_visita_30d"] = (df["p7_gasto_30d"] / df["p6_visitas_30d"]).round(0)
df["prop_visitas_zona"] = (df["p8_visitas_zona"] / df["p6_visitas_30d"]).round(3)

# Nombre de la cafetería
df = df.merge(cafes.rename(columns={"id": "id_cafeteria", "nombre": "cafeteria"}),
              on="id_cafeteria", how="left")

# 4. Controles de calidad (si alguno falla, el script se detiene) ------------------
assert df["id_encuesta"].is_unique, "Hay identificadores repetidos"
assert df["grupo_edad"].notna().all(), "Hay encuestas sin rango de edad"
assert (df["p7_gasto_30d"] >= df["p5_pago_visita"]).all(), "Gasto de 30 días menor que el de la visita"
assert (df["p8_visitas_zona"] <= df["p6_visitas_30d"]).all(), "Más visitas en la zona que en total"
assert (df["p6_visitas_30d"] >= 1).all(), "Visitas en 30 días debe incluir la de hoy"
assert df[escalas].isin([1, 2, 3, 4, 5]).all().all(), "Escala fuera de 1 a 5"
obligatorias = ["p1_motivo", "p2_compania", "p3_permanencia", "p5_tipo_pago"] + numericas + escalas
assert df[obligatorias].notna().all().all(), "Hay preguntas obligatorias vacías"

# 5. Orden de columnas y guardado ---------------------------------------------------
primeras = ["id_encuesta", "id_cafeteria", "cafeteria", "subzona", "fecha", "franja",
            "encuestador", "p12_edad", "grupo_edad"]
df = df[primeras + [c for c in df.columns if c not in primeras]]
df.to_csv(CLEAN / "encuestas_clean.csv", index=False, encoding="utf-8-sig")

diccionario_nuevo = pd.DataFrame([
    ("grupo_edad", "Grupo de edad: Jóvenes 18-29, Adultos 30-45, Mayores 46+ (de p12_edad)"),
    ("cafeteria", "Nombre de la cafetería (de la hoja Cafeterias)"),
    ("subzona", "Subzona de la cafetería"),
    ("gasto_visita_propio", "p5_pago_visita solo si p5_tipo_pago = 'Solo lo mío'; vacío en otro caso"),
    ("gasto_por_visita_30d", "p7_gasto_30d / p6_visitas_30d (pesos)"),
    ("prop_visitas_zona", "p8_visitas_zona / p6_visitas_30d"),
    ("p4_* y p5_compra_pendiente", "1 = Sí, 0 = No"),
    ("p14_estrato", "Estrato 1 a 6; vacío si respondió 'Prefiero no responder'"),
], columns=["variable", "definicion"])
dicc_raw = pd.read_excel(RAW, sheet_name="Diccionario")
with pd.ExcelWriter(CLEAN / "encuestas_clean.xlsx") as w:
    df.to_excel(w, sheet_name="Datos", index=False)
    dicc_raw.to_excel(w, sheet_name="Diccionario", index=False)
    diccionario_nuevo.to_excel(w, sheet_name="Variables nuevas", index=False)

# 6. Resumen por grupo de edad ------------------------------------------------------
resumen = df.groupby("grupo_edad", observed=True).agg(
    n=("id_encuesta", "count"),
    visitas_30d_mediana=("p6_visitas_30d", "median"),
    gasto_visita_propio_mediana=("gasto_visita_propio", "median"),
    gasto_30d_mediana=("p7_gasto_30d", "median"),
    gasto_por_visita_30d_mediana=("gasto_por_visita_30d", "median"),
    dap_mediana=("p10_dap", "median"),
    tazas_dia_media=("p9_tazas_dia", "mean"),
).round(1)
resumen.to_csv(CLEAN / "resumen_por_grupo.csv", encoding="utf-8-sig")
print(resumen.to_string())
print(f"Listo: archivos en {CLEAN}")
