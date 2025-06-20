from flask import Flask, request, render_template, redirect, url_for, flash, session
from supabase import create_client
from routes.auth import auth_bp
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

app.register_blueprint(auth_bp)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def base():
    user = session.get('user')
    username = session.get('username')  # Add this line
    return render_template('base.html', user=user, username=username)

if __name__ == '__main__':
    app.run(debug=True)