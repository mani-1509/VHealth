from flask import Flask, render_template, session, request, jsonify, redirect, url_for
import os
from datetime import datetime
from routes.auth import auth_bp
from supabase import create_client
from openai import OpenAI
import re
from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# auth

app.register_blueprint(auth_bp)

# Supabase client setup

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

#basic route

@app.route('/')
def index():
    user = session.get('user')
    username = session.get('username')
    return render_template('index.html', user=user, username=username)

#analysis route

@app.route('/analyse')
def analyse():
    user = session.get('user')
    username = session.get('username')
    if not user:
        flash('You need to log in first.')
        return redirect(url_for('auth.login'))
    return render_template('analyse.html', user=user, username=username)

@app.route('/analyse_pic', methods=['POST'])
def analyse_pic():
    user = session.get('user')
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    if not request.is_json:
        return jsonify({"message": "Invalid request format"}), 400

    data = request.get_json()
    image_base64 = data.get('image_base64')
    image_url = data.get('image_url')
    user_message = data.get('user_message', "Describe this meal.")
    meal_description = data.get('meal_description', "No description provided.")
    user_goal = data.get('user_goal', "maintain")

    if not image_base64 and not image_url:
        return jsonify({"message": "No image provided"}), 400

    client = OpenAI(
        base_url="https://api.studio.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY")
    )

    content = [{"type": "text", "text": user_message}]
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    else:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}})

    try:
        response = client.chat.completions.create(
            model="google/gemma-3-27b-it",
            messages=[
                {
                    "role": "system",
                    "content": (
                        'You are a certified AI health and fitness coach. '
                        'Always respond in English and use the requested format. '
                        'Analyze the user\'s meal based on this food image description: "{meal_description}" and respond with the following:\n\n'
                        '1. Meal Breakdown: List the main food items and estimate macronutrients (protein, carbs, fats) and calories.\n'
                        '2. Goal Check: If the user\'s goal is "{user_goal}" (e.g. lose weight, build muscle, maintain), tell whether this meal supports it or not.\n'
                        '3. Improvements: Suggest 2-3 tweaks to make the meal more aligned with their goal.\n'
                        '4. Fun Fact: Give one short nutrition tip or myth-busting fact.\n'
                        '5. Mood Insight (Optional): Based on the meal, what kind of mood or energy boost might this food give?\n\n'
                        'Make the tone Gen Z-friendly, slightly funny but still helpful.\n\n'
                        'Example Goals: “lose weight”, “build muscle”, “gluten-free diet”, “high protein”, “clean eating”, “low sugar”, etc.'
                    ).replace("{meal_description}", meal_description).replace("{user_goal}", user_goal)
                },
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        content = response.choices[0].message.content if response.choices else "No response."
        # Extract <think>...</think> and reply
        think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
        think = think_match.group(1).strip() if think_match else ""
        reply = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

    return jsonify({"reply": reply, "thinking": think})

#analyse chat route

@app.route('/analyse-chat')
def analyse_chat():
    user = session.get('user')
    username = session.get('username')
    if not user:
        return redirect(url_for('auth.login'))
    return render_template('analyse-chat.html' , user=user, username=username)

@app.route('/chat_api', methods=['POST'])
def chat_api():
    user = session.get('user')
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    history = data.get('history', [])
    user_message = data.get('user_message', '')

    # If user_message is provided, append it to history
    if user_message:
        history = history + [{"role": "user", "content": user_message}]

    client = OpenAI(
        base_url="https://api.studio.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY")
    )

    response = client.chat.completions.create(
        model="Qwen/Qwen3-30B-A3B",
        messages=history
    )
    content = response.choices[0].message.content if response.choices else "No response."

    # Extract <think>...</think> and reply
    think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
    think = think_match.group(1).strip() if think_match else ""
    reply = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    return jsonify({'reply': reply, 'thinking': think})