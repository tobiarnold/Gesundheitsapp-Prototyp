import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import streamlit as st
import datetime as dt
import pandas as pd
import plotly.express as px
from supabase import create_client

def main():
    st.set_page_config(page_title="Health App", page_icon="⚕️", layout="wide")
    streamlit_style = """
                     <style>
               div.block-container{padding-top:2rem;}
                 """
    st.markdown(streamlit_style, unsafe_allow_html=True)

    # Anmeldung
    names = ["Nici"]
    usernames = ["nici"]
    file_path = Path(__file__).parent / "hashed_pw.pkl"
    with file_path.open("rb") as file:
        hashed_passwords = pickle.load(file)
    authenticator = stauth.Authenticate(names, usernames, hashed_passwords,"health", "abcdef", cookie_expiry_days=30)

    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status == False:
        st.error("Paswwort oder Username inkorrekt")
    if authentication_status == None:
        st.warning("Bitte Nutzername und Passwort eingeben")

    if authentication_status:

        st.title("👩‍🔬 Prototyp Gesundheitstracking")

        #Datenbank Verbindung
        try:
            supabase_url = st.secrets["credentials"]["SUPABASE_URL"]
            supabase_key = st.secrets["credentials"]["SUPABASE_KEY"]
            supabase_client = create_client(supabase_url, supabase_key)
            st.success("Verbindung mit Datenbank hergestellt.")
        except:
            st.error("Es kann keine Verbindung mit der Datenbank hergestellt werden.")

        # Symptome eingeben
        st.info("Bitte Symptome, Datum und Uhrzeit auswählen und Eingaben bestätigen.")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if "symptoms" not in st.session_state:
                st.session_state.symptoms = ["Husten", "Halsschmerzen", "Schluckbeschwerden", "Schwindel", "Schnupfen", "Ohrenschmerzen"]
            new_symptom = st.text_input("Neues Symptom hinzufügen")
            if new_symptom.strip() and new_symptom.strip() not in st.session_state.symptoms:
                st.session_state.symptoms.append(new_symptom)
        with col2:
            selected_symptoms = st.selectbox("Symptome auswählen", st.session_state.symptoms)
            st.markdown("Du hast folgendes Symptom gewählt:")
            if selected_symptoms:
                symptoms_str = "".join(selected_symptoms)
                st.markdown(f"<p style='color:green;'>{symptoms_str}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p>Keine Symptome ausgewählt</p>", unsafe_allow_html=True)  

        # Datum auswählen        
        with col3:
            datum = st.date_input("Datum auswählen", value=dt.date.today())
            st.write("Du hast folgendes Datum gewählt: ", datum)

        # Uhrzeit auswählen
        with col4:
            uhrzeit = st.time_input("Uhrzeit auswählen", dt.time(12, 00))
            st.write("Du hast folgende Uhrzeit ausgewählt ", uhrzeit)

        #Button für Eingabe
        if st.button("Eingaben bestätigen") and selected_symptoms:
            formatted_date = datum.strftime('%Y-%m-%d')
            formatted_time = uhrzeit.strftime('%H:%M:%S')
            new_data = {
                    "symptoms": selected_symptoms,
                    "datum": formatted_date,
                    "uhrzeit": formatted_time}
            try:
                supabase_client.table('health').insert([new_data]).execute()
                st.success("Daten erfolgreich in die Datenbank eingefügt!")
            except Exception as e:
                st.error(f"Fehler beim Einfügen der Daten in die Datenbank: {str(e)}")
        
        st.markdown("--- ")
        col1, col2, col3 = st.columns(3)

        #Datenbank Daten anzeigen
        with col1:
            try:
                st.subheader("💾 Daten aus der Datenbank")
                response = supabase_client.table("health").select("*").execute()
                st.dataframe(response.data)
            except:
                st.write("Daten können nicht geladen werden.")

        #Grafik
        with col2:
            try:
                st.subheader("📊 Anzahl Symptome")
                #symptoms_db = supabase_client.table("health").select("symptoms").execute()
                symptoms_count = pd.DataFrame(response.data)
                symptom_counts = symptoms_count["symptoms"].value_counts().sort_values(ascending=False).reset_index()
                on = st.toggle("Diagramm wechseln")
                if on:
                    fig = px.pie(symptom_counts, names="symptoms", values="count", title="Häufigkeit der Symptome")
                    st.plotly_chart(fig)
                else:
                    fig = px.bar(symptom_counts, x="symptoms", y="count", title="Häufigkeit der Symptome")
                    st.plotly_chart(fig)
            except:
                st.write("Grafik kann nicht geladen werden.")
        
        with col3:
            try:
                datum_counts = symptoms_count["datum"].value_counts().sort_values(ascending=False).reset_index()
                fig = px.bar(datum_counts,  x="datum", y="count", title="Zeitreihe Symptome")
                st.plotly_chart(fig)
            except:
                st.write("Grafik kann nicht geladen werden.")
        st.markdown("--- ")

        #Daten Löschen
        col1, col2 = st.columns([1, 3])
        try:
            with col1:
                st.subheader("⚠️ Daten aus Datenbank löschen")
                id = supabase_client.table("health").select("id").execute()
                id_select= pd.DataFrame(id.data)
                id_auswählen = st.selectbox("ID zum löschen auwählen",(id_select["id"]))
        except:
                st.write("Datenbank kann nicht geladen werden.")
        if st.button("Löschen bestätigen"):
            try:
                supabase_client.table("health").delete().eq('id', id_auswählen).execute()
                st.rerun()
            except:
                st.rerun()

if __name__ == "__main__":
    main()
