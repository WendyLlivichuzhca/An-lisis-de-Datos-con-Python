import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# -------------------------------------------------
# CONFIGURACIÓN INICIAL
# -------------------------------------------------
st.set_page_config(page_title="Guía Práctica 1 - Compras Públicas Ecuador", layout="wide")

# Estilo general (color institucional)
COLOR_PRINCIPAL = "#36BF8D"

# Encabezado principal
st.markdown(f"""
    <div style="background-color:{COLOR_PRINCIPAL};padding:20px;border-radius:12px;margin-bottom:20px;">
        <h1 style="color:white;text-align:center;">📊 Guía Práctica 1 - Análisis de Compras Públicas (Ecuador)</h1>
        <h3 style="color:white;text-align:center;">Wendy Llivichuzhca</h3>
        <p style="color:white;text-align:center;font-size:16px;">
            Esta aplicación permite analizar los datos de compras públicas del Ecuador mediante visualizaciones interactivas 
            y estadísticas descriptivas que facilitan la identificación de patrones, tendencias y relaciones.
        </p>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SIDEBAR: FILTROS
# -------------------------------------------------
st.sidebar.markdown(f"<h2 style='color:{COLOR_PRINCIPAL};'>🎛️ Filtros de Análisis</h2>", unsafe_allow_html=True)

años = [str(a) for a in range(2015, 2026)]
provincias = ["Todos", "AZUAY", "BOLÍVAR", "CAÑAR", "CARCHI", "CHIMBORAZO", "COTOPAXI", "EL ORO",
              "ESMERALDAS", "GALÁPAGOS", "GUAYAS", "IMBABURA", "LOJA", "LOS RÍOS",
              "MANABÍ", "MORONA SANTIAGO", "NAPO", "ORELLANA", "PASTAZA", "PICHINCHA",
              "SANTA ELENA", "SANTO DOMINGO DE LOS TSÁCHILAS", "SUCUMBÍOS", "TUNGURAHUA",
              "ZAMORA CHINCHIPE"]
tipos_contratacion = ["Todos", "Subasta Inversa Electrónica", "Menor Cuantía", "Cotización",
                      "Contratación directa", "Licitación", "Catálogo electrónico", "Bienes y Servicios únicos"]

anio = st.sidebar.selectbox("📅 Año", años)
provincia = st.sidebar.selectbox("📍 Provincia", provincias)
tipo = st.sidebar.selectbox("📂 Tipo de Contratación", tipos_contratacion)
palabra = st.sidebar.text_input("🔎 Palabra clave (opcional)")
btn_cargar = st.sidebar.button("🔄 Cargar datos")

# -------------------------------------------------
# FUNCIÓN PARA CARGAR DATOS
# -------------------------------------------------
@st.cache_data
def cargar_datos(year, region, tipo, palabra):
    url = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/get_analysis"
    params = {
        "year": year,
        "region": None if region == "Todos" else region,
        "type": None if tipo == "Todos" else tipo,
        "keyword": palabra if palabra else None
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return None
    data = resp.json()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

# -------------------------------------------------
# CARGA Y ANÁLISIS
# -------------------------------------------------
if btn_cargar:
    df = cargar_datos(anio, provincia, tipo, palabra)

    if df.empty:
        st.warning("⚠️ La API no devolvió registros con esos parámetros. Prueba con otros valores (por ejemplo: Año 2022, Región vacía, Tipo Obras).")
    else:
        st.success("✅ Datos cargados correctamente.")
        st.markdown(f"**Total de registros obtenidos:** {len(df)}")

        # Estandarización
        rename_map = {"province": "region", "type": "internal_type", "amount": "total", "date": "date"}
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

        # Conversión
        if "total" in df.columns:
            df["total"] = pd.to_numeric(df["total"], errors="coerce")
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["month"] = df["date"].dt.month
            df["year"] = df["date"].dt.year

        df.drop_duplicates(inplace=True)
        df.dropna(subset=["total"], inplace=True)

        # -------------------------------------------------
        # MÉTRICAS GENERALES
        # -------------------------------------------------
        st.markdown(f"<h2 style='color:{COLOR_PRINCIPAL};'>📈 Resumen General</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("📄 Total de registros", len(df))
        col2.metric("💰 Monto total", f"${df['total'].sum():,.2f}")
        col3.metric("💵 Monto promedio", f"${df['total'].mean():,.2f}")

        st.dataframe(df.describe(), use_container_width=True)

        # -------------------------------------------------
        # VISUALIZACIONES
        # -------------------------------------------------
        st.markdown(f"<h2 style='color:{COLOR_PRINCIPAL};'>📊 Visualización de Datos</h2>", unsafe_allow_html=True)

        # a) Monto total por tipo de contratación
        if {"internal_type", "total"}.issubset(df.columns):
            df_tipo = df.groupby("internal_type")["total"].sum().reset_index()
            fig1 = px.bar(df_tipo, x="internal_type", y="total",
                          title="Monto total por tipo de contratación",
                          color_discrete_sequence=[COLOR_PRINCIPAL])
            st.plotly_chart(fig1, use_container_width=True)

        # b) Evolución mensual
        if {"month", "total"}.issubset(df.columns):
            df_mes = df.groupby("month")["total"].sum().reset_index()
            fig2 = px.line(df_mes, x="month", y="total",
                           title="Evolución mensual de montos totales",
                           markers=True, color_discrete_sequence=[COLOR_PRINCIPAL])
            st.plotly_chart(fig2, use_container_width=True)

        # c) Barras apiladas tipo × mes
        if {"month", "internal_type", "total"}.issubset(df.columns):
            df_tipo_mes = df.groupby(["month", "internal_type"])["total"].sum().reset_index()
            fig3 = px.bar(df_tipo_mes, x="month", y="total", color="internal_type", barmode="stack",
                          title="Monto total por tipo de contratación y mes")
            st.plotly_chart(fig3, use_container_width=True)

        # d) Proporción de contratos
        if "internal_type" in df.columns:
            fig4 = px.pie(df, names="internal_type", title="Proporción de contratos por tipo de contratación",
                          color_discrete_sequence=px.colors.sequential.Greens)
            st.plotly_chart(fig4, use_container_width=True)

        # -------------------------------------------------
        # ANÁLISIS POR AÑO
        # -------------------------------------------------
        if {"year", "internal_type", "total"}.issubset(df.columns):
            st.markdown(f"<h2 style='color:{COLOR_PRINCIPAL};'>📆 Análisis por Años</h2>", unsafe_allow_html=True)
            df_year = df.groupby(["year", "internal_type"])["total"].sum().reset_index()
            fig6 = px.bar(df_year, x="year", y="total", color="internal_type", barmode="stack",
                          title="Montos totales por tipo de contratación por año")
            st.plotly_chart(fig6, use_container_width=True)

        # -------------------------------------------------
        # EXPORTACIÓN DE DATOS
        # -------------------------------------------------
        st.markdown(f"<h2 style='color:{COLOR_PRINCIPAL};'>📥 Exportar Datos</h2>", unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Descargar datos como CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"compras_publicas_{anio}.csv",
            mime="text/csv"
        )

        # -------------------------------------------------
        # CONCLUSIONES
        # -------------------------------------------------
        st.markdown(f"<h2 style='color:{COLOR_PRINCIPAL};'>📄 Conclusiones</h2>", unsafe_allow_html=True)
        st.markdown(f"""
        - Los tipos de contratación más utilizados se destacan en los gráficos de barras y pastel.  
        - Se observan variaciones mensuales que reflejan la dinámica de los procesos públicos.  
        - La relación entre monto y número de contratos evidencia concentración de gasto en ciertos tipos de contratación.  
        - La descarga de datos permite un análisis más profundo en herramientas externas.  
        - Esta aplicación facilita la comprensión visual y analítica de la gestión de compras públicas en Ecuador.
        """)

# -------------------------------------------------
# PIE DE PÁGINA
# -------------------------------------------------
st.markdown(f"""
<hr>
<div style="text-align:center; color:gray;">
    <p>Desarrollado por <b>Wendy Llivichuzhca</b> · {datetime.now().strftime("%Y")} · Guía Práctica 1 - Streamlit</p>
</div>
""", unsafe_allow_html=True)
