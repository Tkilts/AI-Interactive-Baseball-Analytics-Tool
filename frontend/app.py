import streamlit as st
import requests

# Configure backend URL
BACKEND_URL = "http://backend:8000"

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None

def login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        data = {"username": email, "password": password}
        try:
            response = requests.post(f"{BACKEND_URL}/token", data=data)
            if response.status_code == 200:
                st.session_state.token = response.json().get("access_token")
                st.success("Logged in successfully!")
            else:
                st.error(f"Login failed: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Login request failed: {e}")

def register():
    st.subheader("Register")
    name = st.text_input("Name")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    if st.button("Register"):
        data = {"name": name, "email": email, "password": password}
        try:
            response = requests.post(f"{BACKEND_URL}/register", data=data)
            if response.status_code == 200:
                st.success("Registered successfully! Please login.")
            else:
                st.error("Registration failed")
        except requests.exceptions.RequestException as e:
            st.error(f"Registration request failed: {e}")

def compare_players():
    st.subheader("Compare MLB Players")
    
    if not st.session_state.token:
        st.warning("Please login first.")
        return

    player1 = st.text_input("First Player Name (e.g., 'Mike Trout')")
    player2 = st.text_input("Second Player Name (e.g., 'Shohei Ohtani')")
    
    if st.button("Compare"):
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        payload = {"player1": player1, "player2": player2}
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/compare_players",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                comparison = response.json().get("comparison", "No comparison available")
                st.subheader("Comparison Result")
                st.write(comparison)
            else:
                st.error(f"Comparison failed: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Comparison request failed: {e}")

def main():
    st.title("MLB Player Value Comparison")
    menu = st.sidebar.selectbox("Menu", ["Login", "Register", "Compare Players"])
    
    if menu == "Login":
        login()
    elif menu == "Register":
        register()
    elif menu == "Compare Players":
        compare_players()

if __name__ == "__main__":
    main()