from flask import Blueprint, request, jsonify, session
from functools import wraps
from openai import OpenAI
import os
from supabase import create_client

health_metric = Blueprint('health_metric', __name__)

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize OpenAI client
client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@health_metric.route('/api/health-metrics', methods=['POST'])
@login_required
def add_health_metric():
    try:
        data = request.json
        user_id = session['user_id']
        insert_data = {
            "user_id": user_id,
            "heart_rate": data.get('heart_rate'),
            "blood_pressure_systolic": data.get('blood_pressure_systolic'),
            "blood_pressure_diastolic": data.get('blood_pressure_diastolic'),
            "calorie_count": data.get('calorie_count')
        }
        result = supabase.table("health_metrics").insert(insert_data).execute()
        if result.data:
            return jsonify({
                "message": "Health metric added successfully",
                "metric_id": result.data[0]['id']
            }), 201
        else:
            return jsonify({"error": "Insert failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@health_metric.route('/api/health-metrics', methods=['GET'])
@login_required
def get_health_metrics():
    try:
        user_id = session['user_id']
        result = supabase.table("health_metrics").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
        metrics = result.data or []
        return jsonify({"metrics": metrics}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@health_metric.route('/api/health-tips', methods=['GET'])
@login_required
def get_health_tips():
    try:
        user_id = session['user_id']
        result = supabase.table("health_metrics").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(1).execute()
        latest_metric = result.data[0] if result.data else None

        if not latest_metric:
            return jsonify({"message": "No health metrics found"}), 404

        prompt = f"""
        Based on the following health metrics:
        Heart Rate: {latest_metric['heart_rate']}
        Blood Pressure: {latest_metric['blood_pressure_systolic']}/{latest_metric['blood_pressure_diastolic']}
        Calorie Count: {latest_metric['calorie_count']}

        Provide personalized health tips and recommendations for improving wellness.
        Respond in HTML format using <h1>, <h2>, <ul>, <li>, <p>, etc. Do NOT use Markdown.
        """

        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        health_tips = completion.choices[0].message.content

        return jsonify({
            "health_tips": health_tips,
            "metrics": {
                "heart_rate": latest_metric['heart_rate'],
                "blood_pressure": f"{latest_metric['blood_pressure_systolic']}/{latest_metric['blood_pressure_diastolic']}",
                "calorie_count": latest_metric['calorie_count']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@health_metric.route('/api/health-metrics/<int:metric_id>', methods=['DELETE'])
@login_required
def delete_health_metric(metric_id):
    try:
        user_id = session['user_id']
        result = supabase.table("health_metrics").delete().eq("id", metric_id).eq("user_id", user_id).execute()
        if result.count > 0:
            return jsonify({"message": "Health metric deleted successfully"}), 200
        else:
            return jsonify({"error": "Health metric not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@health_metric.route('/api/health-metrics/<int:metric_id>', methods=['PUT'])
@login_required
def update_health_metric(metric_id):
    try:
        user_id = session['user_id']
        data = request.json
        update_data = {
            "heart_rate": data.get('heart_rate'),
            "blood_pressure_systolic": data.get('blood_pressure_systolic'),
            "blood_pressure_diastolic": data.get('blood_pressure_diastolic'),
            "calorie_count": data.get('calorie_count')
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}
        result = supabase.table("health_metrics").update(update_data).eq("id", metric_id).eq("user_id", user_id).execute()
        if result.count > 0:
            return jsonify({"message": "Health metric updated successfully"}), 200
        else:
            return jsonify({"error": "Health metric not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@health_metric.route('/api/health-metrics/<int:metric_id>', methods=['GET'])
@login_required
def get_health_metric(metric_id):
    try:
        user_id = session['user_id']
        result = supabase.table("health_metrics").select("*").eq("id", metric_id).eq("user_id", user_id).execute()
        metric = result.data[0] if result.data else None
        if not metric:
            return jsonify({"error": "Health metric not found"}), 404
        return jsonify(metric), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@health_metric.route('/api/health-metrics/summary', methods=['GET'])
@login_required
def get_health_metrics_summary():
    try:
        user_id = session['user_id']
        result = supabase.table("health_metrics").select("*").eq("user_id", user_id).execute()
        metrics = result.data or []
        if not metrics:
            return jsonify({"message": "No health metrics found"}), 404

        heart_rate_avg = sum([m['heart_rate'] for m in metrics if m['heart_rate'] is not None]) / len(metrics)
        bp_systolic_avg = sum([m['blood_pressure_systolic'] for m in metrics if m['blood_pressure_systolic'] is not None]) / len(metrics)
        bp_diastolic_avg = sum([m['blood_pressure_diastolic'] for m in metrics if m['blood_pressure_diastolic'] is not None]) / len(metrics)
        calorie_count_avg = sum([m['calorie_count'] for m in metrics if m['calorie_count'] is not None]) / len(metrics)

        return jsonify({
            "heart_rate_avg": heart_rate_avg,
            "blood_pressure_systolic_avg": bp_systolic_avg,
            "blood_pressure_diastolic_avg": bp_diastolic_avg,
            "calorie_count_avg": calorie_count_avg
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@health_metric.route('/api/health-metrics/summary', methods=['DELETE'])
@login_required
def delete_health_metrics():
    try:
        user_id = session['user_id']
        result = supabase.table("health_metrics").delete().eq("user_id", user_id).execute()
        if result.count > 0:
            return jsonify({"message": "All health metrics deleted successfully"}), 200
        else:
            return jsonify({"message": "No health metrics found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500