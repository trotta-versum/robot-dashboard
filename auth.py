import streamlit as st

USERS = {
    "operatore": {
        "password": "1234",
        "role": "Operatore"
    },
    "responsabile": {
        "password": "abcd",
        "role": "Responsabile"
    },
    "admin": {
        "password": "admin",
        "role": "Amministratore"
    }
}


def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "username" not in st.session_state:
        st.session_state.username = None

    if "role" not in st.session_state:
        st.session_state.role = None


def login_form():
    st.title("Accesso Dashboard Cella Robotica")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Accedi")

        if submitted:
            if username in USERS and USERS[username]["password"] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = USERS[username]["role"]
                st.success("Accesso effettuato con successo.")
                st.rerun()
            else:
                st.error("Credenziali non valide.")


def logout_button():
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()


def require_login():
    init_auth()

    if not st.session_state.authenticated:
        login_form()
        st.stop()


def get_current_role():
    return st.session_state.role


def get_current_user():
    return st.session_state.username
