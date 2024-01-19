import streamlit as st
import requests  # Import the requests library
import os
from dotenv import load_dotenv

# Load environment variables securely
load_dotenv()  # Load .env file (ensure it's in the same directory)
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")

def get_access_token(code):
    url = "https://oauth2.googleapis.com/token"
    params = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "http://localhost:8501",  # Adjust redirect_uri if needed
        "grant_type": "authorization_code",
    }
    response = requests.post(url, data=params)
    return response.json().get("access_token")

def get_user_info(access_token):
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json()

def login():
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&scope=openid%20email&redirect_uri=http://localhost:8501"  # Adjust redirect_uri if needed
    st.session_state["auth_url"] = auth_url
    return st.query_params.get("code")

def verify_token(code):
    try:
        access_token = get_access_token(code)
        user_info = get_user_info(access_token)
        st.session_state["user_info"] = user_info
        st.session_state["user_name"] = user_info.get("name", "")
        st.success("Logged in successfully!")
    except ValueError as e:
        st.error(f"Invalid token: {e}")



def verify_login():
    user_name = None  # Initialize user_name variable

    if "code" not in st.session_state:
        code = login()
        if code:
            user_name = verify_token(code)  # Update user_name with the returned value
            return user_name  # Exit early to avoid displaying the "Login with Google" title
    else:
        user_name = verify_token(st.session_state.code)

    if user_name:
        st.title(f"Welcome, {user_name}!")
        # Display additional features for logged-in users
    else:
        st.caption("Login with Google")
        st.markdown(f'<a href="{st.session_state["auth_url"]}" target="_self">Click here to sign in with Google</a>', unsafe_allow_html=True)
