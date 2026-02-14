"""API utility functions for communicating with Django backend"""
import requests
import streamlit as st
import os

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000/api")

def register_user(username: str, email: str, password: str, password_confirm: str):
    """Register a new user"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/authentication/register/",
            json={
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password_confirm
            },
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        error_msg = "Registration failed"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = str(error_data)
            except:
                error_msg = str(e)
        return {"success": False, "error": error_msg}

def login_user(username: str, password: str):
    """Login user and get JWT tokens"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/auth/login/",
            json={"username": username, "password": password},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return {
            "success": True,
            "access_token": data.get("access"),
            "refresh_token": data.get("refresh")
        }
    except requests.exceptions.RequestException as e:
        error_msg = "Login failed"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = str(error_data)
            except:
                error_msg = str(e)
        return {"success": False, "error": error_msg}

def get_current_user(access_token: str):
    """Get current user information"""
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/authentication/me/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def list_agents(access_token: str):
    """Get list of user's agents"""
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/agents/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        # Django REST framework pagination returns {'results': [...]}
        agents = data.get('results', data) if isinstance(data, dict) else data
        return {"success": True, "data": agents}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def create_agent(access_token: str, name: str, system_prompt: str, conversation_model: str = "llama3.2:1b"):
    """Create a new agent"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/agents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": name,
                "system_prompt": system_prompt,
                "conversation_model": conversation_model
            },
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        error_msg = "Failed to create agent"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = str(error_data)
            except:
                error_msg = str(e)
        return {"success": False, "error": error_msg}

def get_agent(access_token: str, agent_id: str):
    """Get agent details"""
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/agents/{agent_id}/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def update_agent(access_token: str, agent_id: str, **kwargs):
    """Update agent"""
    try:
        response = requests.patch(
            f"{DJANGO_API_URL}/agents/{agent_id}/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=kwargs,
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def delete_agent(access_token: str, agent_id: str):
    """Delete agent"""
    try:
        response = requests.delete(
            f"{DJANGO_API_URL}/agents/{agent_id}/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def start_session(access_token: str, agent_id: str):
    """Start a new session for an agent"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/agents/{agent_id}/start_session/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def list_sessions(access_token: str):
    """Get list of sessions"""
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/agents/sessions/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        # Django REST framework pagination returns {'results': [...]}
        sessions = data.get('results', data) if isinstance(data, dict) else data
        return {"success": True, "data": sessions}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_session(access_token: str, session_id: str):
    """Get session details"""
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/agents/sessions/{session_id}/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def end_session(access_token: str, session_id: str):
    """End a session"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/agents/sessions/{session_id}/end_session/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_session_logs(access_token: str, session_id: str):
    """Get session logs"""
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/agents/sessions/{session_id}/logs/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
