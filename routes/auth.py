from flask import Blueprint, request, redirect, url_for, render_template, flash, session
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

auth_bp = Blueprint('auth', __name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        try:
            # Check if username exists
            exists = supabase.table("profiles").select("id").eq("username", username).execute()
            if exists.data:
                flash('Username already taken.')
                return render_template('signup.html')
            # Create user in Supabase Auth
            result = supabase.auth.sign_up({"email": email, "password": password})
            if result.user:
                # Insert into profiles table
                supabase.table("profiles").insert({
                    "id": result.user.id,
                    "username": username,
                    "full_name": "",
                }).execute()
                flash('Signup successful! Please log in.')
                return redirect(url_for('auth.login'))
            else:
                error_message = result.error.message if result.error else "Unknown error"
                flash('Signup failed: ' + error_message)
        except Exception as e:
            flash('Signup failed: ' + str(e))
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        try:
            # Try to find by username
            profile_resp = supabase.table("profiles").select("id, username, full_name").eq("username", identifier).execute()
            if profile_resp.data and len(profile_resp.data) == 1:
                user_id = profile_resp.data[0]['id']
                user = supabase.table("auth.users").select("email").eq("id", user_id).single().execute()
                email = user.data['email']
            else:
                # Assume identifier is email
                email = identifier
            result = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if result.session:
                session['user'] = email
                session['user_id'] = result.user.id
                # Optionally, fetch and store username in session
                profile = supabase.table("profiles").select("username").eq("id", result.user.id).single().execute()
                if profile.data:
                    session['username'] = profile.data['username']
                flash('Login successful!')
                return redirect(url_for('index'))
            else:
                error_message = result.error.message if result.error else "Unknown error"
                flash('Login failed: ' + error_message)
        except Exception as e:
            flash('Login failed: ' + str(e))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    try:
        supabase.auth.sign_out()
        session.pop('user', None)
        flash('Logout successful!')
    except Exception as e:
        flash('Logout failed: ' + str(e))
    return redirect(url_for('index'))