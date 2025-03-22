import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import date
import os

# Streamlit-Konfiguration: Muss zu Beginn des Skripts aufgerufen werden.
st.set_page_config(page_title="Milcheinlieferung", layout="centered")

# Erweiterte CSS-Regeln für ein modernes, dunkles Design, weiße Eingabetexte und speziell für deaktivierte Felder
st.markdown(
    """
    <style>
    /* Globaler Hintergrund und Textfarbe */
    .stApp {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    /* Überschriften anpassen */
    h1, h2, h3, h4, h5, h6 {
        color: #E0E0E0;
    }
    /* Eingabefelder: Hintergrund und weiße Schrift */
    input, 
    .stTextInput > div > div > input,
    .stDateInput input,
    .stSelectbox input,
    select,
    textarea {
        background-color: #3C3C3C !important;
        color: #FFFFFF !important;
        border: 1px solid #555555 !important;
    }
    /* Sicherstellen, dass auch deaktivierte Eingabefelder weiß bleiben */
    input:disabled, 
    .stTextInput > div > div > input:disabled {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    /* Button anpassen */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        cursor: pointer;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    /* Dataframe Styling */
    .css-1outpf7, .stDataTable {
        background-color: #3C3C3C;
        color: #FFFFFF;
    }
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #2E2E2E;
    }
    ::-webkit-scrollbar-thumb {
        background: #555555;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #777777;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# JavaScript-Snippet, das beim Klicken im Nummer-Feld den Fokus auf das "Menge"-Feld setzt
st.markdown(
    """
    <script>
    // Warte, bis alle Elemente geladen sind
    document.addEventListener("DOMContentLoaded", function() {
        // Suche nach dem Container der Selectbox (nummer)
        const listboxes = window.parent.document.querySelectorAll('div[role="listbox"]');
        if(listboxes.length > 0) {
            // Hier wird der erste Listbox-Container genutzt – ggf. anpassen, falls mehrere vorhanden sind.
            listboxes[0].addEventListener("click", function() {
                setTimeout(function(){
                    // Suche das Input-Feld mit dem Placeholder "Menge eingeben"
                    const inputs = window.parent.document.querySelectorAll('input');
                    for(let i = 0; i < inputs.length; i++){
                        if(inputs[i].placeholder === "Menge eingeben"){
                            inputs[i].focus();
                            break;
                        }
                    }
                }, 500); // kurze Verzögerung, damit sich die Auswahl abgeschlossen hat
            });
        }
    });
    </script>
    """,
    unsafe_allow_html=True
)

# Excel-Datei (sicherstellen, dass sie existiert)
EXCEL_FILE = "milcheinlieferungen.xlsx"
if not os.path.exists(EXCEL_FILE):
    # Erstelle eine leere Excel-Datei mit den Spaltenüberschriften
    pd.DataFrame(columns=["Datum", "Nummer", "Lieferant", "Menge (L)"]).to_excel(EXCEL_FILE, index=False)

# MySQL-Datenbankverbindung mit Fehlerbehandlung
def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="9058",  # Hier dein Passwort einfügen
            database="milcheinlieferungen"
        )
        return conn
    except Error as e:
        st.error(f"❌ Datenbankverbindungsfehler: {e}")
        return None

# Funktion zum Laden der Daten aus Excel (persistente Daten)
def load_data():
    try:
        return pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Datum", "Nummer", "Lieferant", "Menge (L)"])
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Excel-Datei: {e}")
        return pd.DataFrame(columns=["Datum", "Nummer", "Lieferant", "Menge (L)"])

# Funktion zum Speichern der Daten in Excel
def save_data(data):
    try:
        data.to_excel(EXCEL_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"❌ Fehler beim Speichern der Excel-Datei: {e}")
        return False

# Funktion zum Speichern der Daten in MySQL mit Fehlerbehandlung
def save_to_db(datum, nummer, lieferant, milchmenge):
    conn = connect_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO entries (datum, nummer, lieferant, menge)
            VALUES (%s, %s, %s, %s)
            """,
            (datum, nummer, lieferant, milchmenge)
        )
        conn.commit()
        return True
    except Error as e:
        st.error(f"❌ Fehler beim Speichern in der Datenbank: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

# Funktion zum Löschen eines Eintrags aus MySQL mit Fehlerbehandlung
def delete_from_db(datum, nummer, milchmenge):
    conn = connect_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM entries WHERE datum=%s AND nummer=%s AND menge=%s
            """,
            (datum, nummer, milchmenge)
        )
        conn.commit()
        return True
    except Error as e:
        st.error(f"❌ Fehler beim Löschen aus der Datenbank: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

# Zentrale Funktion zum synchronisierten Speichern in Excel und Datenbank
def save_entry(datum, nummer, lieferant, milchmenge):
    # Excel-Speicherung
    df = load_data()
    new_entry = pd.DataFrame([[datum, nummer, lieferant, milchmenge]],
                             columns=["Datum", "Nummer", "Lieferant", "Menge (L)"])
    df = pd.concat([df, new_entry], ignore_index=True)
    excel_success = save_data(df)

    # Datenbank-Speicherung
    db_success = save_to_db(datum, nummer, lieferant, milchmenge)

    if excel_success and db_success:
        st.success("✅ Eintrag synchronisiert gespeichert!")
    else:
        st.error("⚠️ Synchronisationsproblem: Überprüfe Excel- und Datenbankeintrag.")

# Zentrale Funktion zum synchronisierten Löschen in Excel und Datenbank
def delete_entry(datum, nummer, milchmenge):
    df = load_data()
    condition = (df["Datum"] == datum) & (df["Nummer"] == nummer) & (df["Menge (L)"] == milchmenge)
    if condition.sum() == 0:
        st.warning("⚠️ Eintrag in Excel nicht gefunden.")
        excel_success = False
    else:
        df = df[~condition].reset_index(drop=True)
        excel_success = save_data(df)

    db_success = delete_from_db(datum, nummer, milchmenge)

    if excel_success and db_success:
        st.success("🗑️ Eintrag synchronisiert gelöscht!")
    else:
        st.error("⚠️ Synchronisationsproblem beim Löschen: Überprüfe Excel- und Datenbankeintrag.")

# Lieferanten-Daten
lieferanten_dict = {
    "1": "Fritsche Herbert",
    "2": "Inauen Roman",
    "4": "Neff Hansueli",
    "13": "Inauen Silvan",
    "17": "Fässler Christian",
    "19": "Sutter Adrian",
    "21": "Fuchs Urs",
    "23": "Inauen Severin",
    "30": "Inauen Armin",
    "102": "Inauen Roman"
}

# UI: Titel und Trennlinien
st.title("🐄 Milcheinlieferungen")
st.markdown("---")

# Layout für Eingabefelder in zwei Spalten
col1, col2 = st.columns(2)

with col1:
    datum = st.date_input("📅 Datum", value=date.today())
    nummer_options = ["Bitte wählen", "1", "2", "4", "13", "17", "19", "21", "23", "30", "102"]
    nummer = st.selectbox("🔢 Nummer", options=nummer_options)
    
with col2:
    # Direkt den Lieferanten aus der Auswahl ableiten:
    lieferant = lieferanten_dict.get(nummer, "") if nummer != "Bitte wählen" else ""
    st.text_input("🏠 Lieferant", value=lieferant, disabled=True)

milch_input = st.text_input(
    "🥛 Milchmenge (L)",
    value="",
    placeholder="Menge eingeben",
    help="Bitte in Liter mit einer Dezimalstelle eingeben"
)

if st.button("💾 Speichern", use_container_width=True):
    if milch_input and nummer != "Bitte wählen":
        try:
            milchmenge = float(milch_input)
        except ValueError:
            st.error("⚠️ Bitte eine gültige Zahl für die Milchmenge eingeben.")
        else:
            save_entry(datum, nummer, lieferant, milchmenge)
    else:
        st.error("⚠️ Bitte alle Felder korrekt ausfüllen.")

st.markdown("---")
st.subheader("📜 Bisherige Einträge")

# Laden und Anzeigen der persistierten Daten aus der Excel-Datei
data = load_data()
if not data.empty:
    selected_index = st.multiselect("🗑️ Zu löschenden Eintrag auswählen", data.index.tolist())
    st.dataframe(data, height=300, use_container_width=True)
    if st.button("❌ Löschen", use_container_width=True) and selected_index:
        for index in selected_index:
            row = data.loc[index]
            delete_entry(row["Datum"], row["Nummer"], row["Menge (L)"])
        st.experimental_rerun()
else:
    st.info("ℹ️ Keine Einträge vorhanden.")
