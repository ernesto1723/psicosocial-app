import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText

# Configuración de la página
st.set_page_config(page_title="Análisis Psicosocial", layout="wide")
st.title("🧠 Sistema de Evaluación Psicosocial")
st.write("Sube un archivo Excel con los resultados de la encuesta para obtener análisis, gráficos y diagnóstico.")

# Upload
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

# Dimensiones
ECON_ITEMS = ['E1','E2','E3','E4','E5']
SOC_ITEMS = ['S1','S2','S3','S4','S5']
PSY_ITEMS = ['P1','P2','P3','P4','P5','P6','P7']

# Funciones
def score_dimension(row, items):
    vals = row[items].astype(float)
    raw = vals.sum()
    max_raw = len(items)*4
    pct = (raw/max_raw)*100
    return pct

def diagnostico(e, s, p, p4):
    score_global = np.mean([e,s,p])
    if score_global >= 70 or p4 >= 2:
        return score_global, "🔴 GRAVE", "Requiere atención profesional urgente (psicología o psiquiatría)."
    elif score_global >= 40:
        return score_global, "🟡 PREOCUPANTE", "Se recomienda asesoría psicosocial y manejo del estrés."
    else:
        return score_global, "🟢 NORMAL", "Mantener hábitos saludables, ejercicio, descanso y redes de apoyo."

# Función SMTP para alertas
def enviar_alerta_correo(usuario_id, nivel, recomendacion):
    smtp_host = "smtp-relay.brevo.com"
    smtp_port = 587
    smtp_user = "9d56cc001@smtp-brevo.com"      # tu usuario SMTP
    smtp_pass = "avX8BxfdgyVh0UGT"              # tu clave SMTP
    correo_destino = "correo_del_psicologo@ejemplo.com"  # cambia por tu destinatario

    asunto = f"🚨 Alerta Psicosocial - Caso {usuario_id}"
    cuerpo = f"""
Se ha detectado un caso con nivel: {nivel}

ID del individuo: {usuario_id}
Recomendación inmediata:
{recomendacion}

Por favor revisar este caso lo antes posible.
    """

    msg = MIMEText(cuerpo)
    msg["From"] = smtp_user
    msg["To"] = correo_destino
    msg["Subject"] = asunto

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, correo_destino, msg.as_string())
        server.quit()
        print("Correo enviado correctamente")
    except Exception as e:
        print("Error enviando correo:", e)

# --------------------
# Bloque Excel
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    required_cols = ['respondent_id'] + ECON_ITEMS + SOC_ITEMS + PSY_ITEMS
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Faltan columnas en el Excel: {missing}")
    else:
        st.success("Archivo cargado correctamente ✔")
        resultados = []

        for _, row in df.iterrows():
            rid = row["respondent_id"]
            econ = score_dimension(row, ECON_ITEMS)
            soc = score_dimension(row, SOC_ITEMS)
            psy = score_dimension(row, PSY_ITEMS)
            p4 = row["P4"]

            score_global, nivel, recomendacion = diagnostico(econ, soc, psy, p4)
            resultados.append([rid, econ, soc, psy, score_global, nivel, recomendacion])

            # Enviar alerta si es grave
            if nivel == "🔴 GRAVE":
                enviar_alerta_correo(rid, nivel, recomendacion)

            # Gráfico individual
            fig, ax = plt.subplots(figsize=(4,3))
            categorias = ["Económico", "Social", "Psicológico"]
            valores = [econ, soc, psy]
            ax.bar(categorias, valores)
            ax.set_ylim(0,100)
            ax.set_title(f"Perfil Psicosocial - ID {rid}")
            st.pyplot(fig)

            st.info(f"""
            ### 🧍 Respondiente {rid}
            **Estado:** {nivel}  
            **Score Global:** {score_global:.1f}%  
            **Recomendación:** {recomendacion}
            """)

        resultados_df = pd.DataFrame(resultados, columns=[
            "ID", "Económico %", "Social %", "Psicológico %", "Global", "Nivel", "Recomendación"
        ])

        st.subheader("📄 Resultados Completos")
        st.dataframe(resultados_df)

        st.download_button(
            label="Descargar resultados en Excel",
            data=resultados_df.to_csv(index=False).encode("utf-8"),
            file_name="resultados_psicosocial.csv",
            mime="text/csv"
        )

# --------------------
# Bloque Test interactivo
st.header("📝 Test Psicosocial Interactivo")
modo = st.radio("Elige cómo deseas evaluar:", ["Subir archivo Excel", "Realizar test interactivo"])

if modo == "Realizar test interactivo":
    st.subheader("Preguntas del Test")

    # Dimensión Económica
    st.write("### 💰 Dimensión Económica")
    econ = [st.select_slider(f"E{i}: Nivel de estabilidad económica", options=[0,1,2,3,4]) for i in range(1,6)]

    # Dimensión Social
    st.write("### 🤝 Dimensión Social")
    soc = [st.select_slider(f"S{i}: Relaciones y red de apoyo", options=[0,1,2,3,4]) for i in range(1,6)]

    # Dimensión Psicológica
    st.write("### 🧠 Dimensión Psicológica")
    psy = [st.select_slider(f"P{i}: Estado emocional", options=[0,1,2,3,4]) for i in range(1,8)]

    if st.button("Obtener diagnóstico"):
        econ_score = sum(econ)/(5*4)*100
        soc_score = sum(soc)/(5*4)*100
        psy_score = sum(psy)/(7*4)*100
        p4 = psy[3]  # P4

        # Diagnóstico
        if max(econ_score, soc_score, psy_score) >= 70 or p4 >= 2:
            nivel = "🔴 GRAVE"
            recomendacion = "Se requiere atención profesional urgente."
        elif max(econ_score, soc_score, psy_score) >= 40:
            nivel = "🟡 PREOCUPANTE"
            recomendacion = "Recomendable asesoría psicosocial y manejo emocional."
        else:
            nivel = "🟢 NORMAL"
            recomendacion = "Seguir hábitos saludables y manejo del estrés."

        # Enviar alerta si es grave
        if nivel == "🔴 GRAVE":
            enviar_alerta_correo("TEST_INTERACTIVO", nivel, recomendacion)

        # Mostrar resultados
        st.success(f"**Estado general: {nivel}**")
        st.write(f"### Resultado del Test")
        st.write(f"**Económico:** {econ_score:.1f}%")
        st.write(f"**Social:** {soc_score:.1f}%")
        st.write(f"**Psicológico:** {psy_score:.1f}%")
        st.info(recomendacion)

        # Gráfico
        fig, ax = plt.subplots()
        categorias = ["Económico", "Social", "Psicológico"]
        valores = [econ_score, soc_score, psy_score]
        ax.bar(categorias, valores)
        ax.set_ylim(0,100)
        st.pyplot(fig)

        # Guardar en CSV
        resultado = pd.DataFrame([{
            "Económico": econ_score,
            "Social": soc_score,
            "Psicológico": psy_score,
            "Nivel": nivel,
            "Recomendación": recomendacion
        }])
        st.download_button(
            "Descargar resultado",
            resultado.to_csv(index=False).encode("utf-8"),
            "resultado_individual.csv",
            "text/csv",
        )
