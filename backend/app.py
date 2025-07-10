import os
import json
from flask import Flask, redirect, session, request, jsonify, Blueprint, current_app
from flask_cors import CORS
from google_auth_oauthlib.flow import Flow
import requests
from datetime import datetime
from flask_caching import Cache

BOARD_EMAIL = "manoharareddyp97@gmail.com"

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)

# --- Redis Cache Configuration ---
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_DEFAULT_TIMEOUT'] = 60  # 60 seconds default
cache = Cache(app)

with open("client_secret.json") as f:
    oauth_config = json.load(f)

# In-memory data structures
app.config['PROJECTS'] = []
app.config['CREDITS'] = []

def find_project(project_id):
    for project in app.config['PROJECTS']:
        if project["project_id"] == project_id:
            return project
    return None

def find_credit(credit_id):
    for credit in app.config['CREDITS']:
        if credit["credit_id"] == credit_id:
            return credit
    return None

def invalidate_all_caches():
    cache.delete('all_projects')
    cache.delete('all_credits')
    cache.delete('projectwise_credits')
    cache.delete('creditwise_history')
    cache.delete('beckn_search')
    # Invalidate user-specific caches if needed (example for 10 users)
    for credit in app.config['CREDITS']:
        cache.delete(f"user_credits_{credit['owner_email']}")
    for user in set([p['owner_email'] for p in app.config['PROJECTS']]):
        cache.delete(f"user_projects_{user}")

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get("name")
    user_email = data.get("user_email")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if not name or not user_email:
        return jsonify({"status": "error", "message": "Project name and user_email required"}), 400
    if user_email == BOARD_EMAIL:
        return jsonify({"status": "error", "message": "Board user cannot register projects."}), 403
    project_id = f"proj{int(datetime.now().timestamp())}"
    project = {
        "project_id": project_id,
        "name": name,
        "status": "registered",
        "owner_email": user_email,
        "latitude": latitude,
        "longitude": longitude
    }
    app.config['PROJECTS'].append(project)
    invalidate_all_caches()
    return jsonify({"status": "success", "project_id": project_id})

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    project_id = data.get("project_id")
    verifier_email = data.get("verifier_email")
    if verifier_email != BOARD_EMAIL:
        return jsonify({"status": "error", "message": "Unauthorized verifier"}), 403
    project = find_project(project_id)
    if not project:
        return jsonify({"status": "error", "message": "Project not found"}), 404
    project["status"] = "verified"
    invalidate_all_caches()
    return jsonify({"status": "verified", "project_id": project_id})

@app.route('/projects', methods=['GET'])
@cache.cached(key_prefix='all_projects')
def get_all_projects():
    return jsonify(app.config['PROJECTS'])

@app.route('/projects/user', methods=['GET'])
@cache.cached(timeout=60, key_prefix=lambda: f"user_projects_{request.args.get('user_email')}")
def get_user_projects():
    user_email = request.args.get("user_email")
    return jsonify([p for p in app.config['PROJECTS'] if p["owner_email"] == user_email])

@app.route('/issue_credit', methods=['POST'])
def issue():
    data = request.json
    project_id = data.get("project_id")
    amount = data.get("amount")
    owner_email = data.get("owner_email")
    if not project_id or not amount or not owner_email:
        return jsonify({"status": "error", "message": "project_id, amount and owner_email required"}), 400
    if owner_email == BOARD_EMAIL:
        return jsonify({"status": "error", "message": "Board user cannot own credits."}), 403
    project = find_project(project_id)
    if not project:
        return jsonify({"status": "error", "message": "Project not found"}), 404
    if project["status"] != "verified":
        return jsonify({"status": "error", "message": "Project not verified. Cannot issue credits."}), 400
    credit = {
        "credit_id": f"cc{len(app.config['CREDITS'])+1}",
        "project_id": project_id,
        "amount": amount,
        "issuer_email": owner_email,
        "owner_email": owner_email,
        "status": "issued",
        "for_sale": False,
        "blocked": False,
        "history": [
            {
                "action": "issued",
                "by": owner_email,
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
    app.config['CREDITS'].append(credit)
    invalidate_all_caches()
    return jsonify({"status": "issued", "credit": credit})

@app.route('/list_credits', methods=['GET'])
@cache.cached(timeout=30, key_prefix='all_credits')
def list_all():
    user_email = request.args.get("user_email")
    is_board = user_email == BOARD_EMAIL
    if is_board:
        return jsonify(app.config['CREDITS'])
    if user_email:
        return jsonify([c for c in app.config['CREDITS'] if c["owner_email"] == user_email])
    return jsonify([c for c in app.config['CREDITS'] if c["for_sale"] and not c["blocked"] and c["status"] == "verified"])

@app.route('/credits/user', methods=['GET'])
@cache.cached(timeout=30, key_prefix=lambda: f"user_credits_{request.args.get('user_email')}")
def user_credits():
    user_email = request.args.get("user_email")
    return jsonify([c for c in app.config['CREDITS'] if c["owner_email"] == user_email])

@app.route('/set_for_sale', methods=['POST'])
def set_for_sale():
    data = request.json
    credit_id = data.get("credit_id")
    user_email = data.get("user_email")
    credit = find_credit(credit_id)
    if not credit:
        return jsonify({"status": "error", "message": "Credit not found"}), 404
    if credit["owner_email"] != user_email:
        return jsonify({"status": "error", "message": "Only the current owner can put credit for sale."}), 403
    if credit["blocked"]:
        return jsonify({"status": "error", "message": "Credit is blocked by board."}), 403
    if credit["status"] != "verified":
        return jsonify({"status": "error", "message": "Credit must be verified by board before sale."}), 403
    credit["for_sale"] = True
    credit["history"].append({
        "action": "put_for_sale",
        "by": user_email,
        "timestamp": datetime.now().isoformat()
    })
    invalidate_all_caches()
    return jsonify({"status": "success", "credit": credit})

@app.route('/remove_from_sale', methods=['POST'])
def remove_from_sale():
    data = request.json
    credit_id = data.get("credit_id")
    user_email = data.get("user_email")
    credit = find_credit(credit_id)
    if not credit:
        return jsonify({"status": "error", "message": "Credit not found"}), 404
    if credit["owner_email"] != user_email:
        return jsonify({"status": "error", "message": "Only the current owner can remove credit from sale."}), 403
    credit["for_sale"] = False
    credit["history"].append({
        "action": "removed_from_sale",
        "by": user_email,
        "timestamp": datetime.now().isoformat()
    })
    invalidate_all_caches()
    return jsonify({"status": "success", "credit": credit})

@app.route('/verify_credit', methods=['POST'])
def verify_credit():
    data = request.json
    credit_id = data.get("credit_id")
    verifier_email = data.get("verifier_email")
    if verifier_email != BOARD_EMAIL:
        return jsonify({"status": "error", "message": "Unauthorized verifier"}), 403
    credit = find_credit(credit_id)
    if not credit:
        return jsonify({"status": "error", "message": "Credit not found"}), 404
    credit["status"] = "verified"
    credit["history"].append({
        "action": "verified",
        "by": verifier_email,
        "timestamp": datetime.now().isoformat()
    })
    invalidate_all_caches()
    return jsonify({"status": "verified", "credit_id": credit_id})

@app.route('/purchase_credit', methods=['POST'])
def purchase_credit():
    data = request.json
    credit_id = data.get("credit_id")
    buyer_email = data.get("buyer_email")
    if not credit_id or not buyer_email:
        return jsonify({"status": "error", "message": "credit_id and buyer_email required"}), 400
    if buyer_email == BOARD_EMAIL:
        return jsonify({"status": "error", "message": "Board user cannot purchase credits."}), 403
    credit = find_credit(credit_id)
    if not credit:
        return jsonify({"status": "error", "message": "Credit not found"}), 404
    project = find_project(credit["project_id"])
    if not project or project["status"] != "verified":
        return jsonify({"status": "error", "message": "Project not verified. Cannot purchase credits."}), 400
    if credit["status"] != "verified":
        return jsonify({"status": "error", "message": "Credit not verified by board. Cannot purchase credits."}), 400
    if not credit["for_sale"]:
        return jsonify({"status": "error", "message": "Credit not for sale."}), 403
    if credit["blocked"]:
        return jsonify({"status": "error", "message": "Credit is blocked by board."}), 403
    credit["owner_email"] = buyer_email
    credit["for_sale"] = False
    credit["history"].append({
        "action": "purchased",
        "by": buyer_email,
        "timestamp": datetime.now().isoformat()
    })
    invalidate_all_caches()
    return jsonify({"status": "success", "credit": credit})

@app.route('/block_credit', methods=['POST'])
def block_credit():
    data = request.json
    credit_id = data.get("credit_id")
    board_email = data.get("board_email")
    if board_email != BOARD_EMAIL:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    credit = find_credit(credit_id)
    if not credit:
        return jsonify({"status": "error", "message": "Credit not found"}), 404
    credit["blocked"] = True
    credit["for_sale"] = False
    credit["history"].append({
        "action": "blocked",
        "by": board_email,
        "timestamp": datetime.now().isoformat()
    })
    invalidate_all_caches()
    return jsonify({"status": "blocked", "credit": credit})

@app.route('/release_credit', methods=['POST'])
def release_credit():
    data = request.json
    credit_id = data.get("credit_id")
    board_email = data.get("board_email")
    if board_email != BOARD_EMAIL:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    credit = find_credit(credit_id)
    if not credit:
        return jsonify({"status": "error", "message": "Credit not found"}), 404
    credit["blocked"] = False
    credit["history"].append({
        "action": "released",
        "by": board_email,
        "timestamp": datetime.now().isoformat()
    })
    invalidate_all_caches()
    return jsonify({"status": "released", "credit": credit})

@app.route('/board/projectwise_credits', methods=['GET'])
@cache.cached(key_prefix='projectwise_credits')
def board_projectwise_credits():
    projectwise = []
    for project in app.config['PROJECTS']:
        project_credits = [c for c in app.config['CREDITS'] if c["project_id"] == project["project_id"]]
        project_dict = dict(project)
        credits_list = [dict(c) for c in project_credits]
        projectwise.append({
            "project": project_dict,
            "credits": credits_list
        })
    return jsonify(projectwise)

@app.route('/board/creditwise_history', methods=['GET'])
@cache.cached(key_prefix='creditwise_history')
def board_creditwise_history():
    return jsonify(app.config['CREDITS'])

@app.route("/login")
def login():
    flow = Flow.from_client_config(
        oauth_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
        redirect_uri="http://localhost:5000/oauth2callback"
    )
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return jsonify({"auth_url": authorization_url})

@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("state") or request.args.get("state") or ""
    flow = Flow.from_client_config(
        oauth_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
        state=state,
        redirect_uri="http://localhost:5000/oauth2callback"
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["google_token"] = credentials.token
    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"}
    )
    userinfo = userinfo_response.json()
    session["user"] = userinfo
    return redirect(f"http://localhost:3000?user={userinfo['email']}")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("http://localhost:3000")

# --- Beckn Protocol Integration ---

beckn_api = Blueprint('beckn_api', __name__)

def credit_to_beckn_item(credit):
    return {
        "id": credit["credit_id"],
        "descriptor": {"name": f"Credit {credit['credit_id']}"},
        "tags": [
            {"code": "project_id", "value": credit["project_id"]},
            {"code": "owner", "value": credit["owner_email"]},
            {"code": "status", "value": credit["status"]},
        ]
    }

@beckn_api.route('/beckn/search', methods=['POST'])
@cache.cached(timeout=30, key_prefix='beckn_search')
def beckn_search():
    credits = current_app.config['CREDITS']
    available_credits = [c for c in credits if c['status'] == 'verified' and not c['blocked'] and c['for_sale']]
    items = [credit_to_beckn_item(c) for c in available_credits]
    return jsonify({"message": "Beckn search", "items": items})

@beckn_api.route('/beckn/select', methods=['POST'])
def beckn_select():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['credit_id'] == credit_id), None)
    if not credit or credit['status'] != 'verified' or credit['blocked'] or not credit['for_sale']:
        return jsonify({"error": "Credit not available"}), 404
    return jsonify({"message": "Credit selected", "item": credit_to_beckn_item(credit)})

@beckn_api.route('/beckn/init', methods=['POST'])
def beckn_init():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['credit_id'] == credit_id), None)
    if not credit or credit['status'] != 'verified' or credit['blocked'] or not credit['for_sale']:
        return jsonify({"error": "Credit not available"}), 404
    return jsonify({"message": "Transaction initialized", "item": credit_to_beckn_item(credit)})

@beckn_api.route('/beckn/confirm', methods=['POST'])
def beckn_confirm():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    buyer = data.get("buyer", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['credit_id'] == credit_id), None)
    if not credit or credit['status'] != 'verified' or credit['blocked'] or not credit['for_sale']:
        return jsonify({"error": "Credit not available"}), 404
    credit['owner_email'] = buyer
    credit['for_sale'] = False
    credit['history'].append({"owner": buyer, "action": "beckn_transfer", "timestamp": datetime.now().isoformat()})
    invalidate_all_caches()
    return jsonify({"message": "Transaction confirmed", "item": credit_to_beckn_item(credit)})

@beckn_api.route('/beckn/status', methods=['POST'])
@cache.cached(timeout=30, key_prefix=lambda: f"beckn_status_{request.json.get('item', {}).get('id')}")
def beckn_status():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['credit_id'] == credit_id), None)
    if not credit:
        return jsonify({"error": "Credit not found"}), 404
    return jsonify({"item": credit_to_beckn_item(credit), "history": credit.get("history", [])})

app.register_blueprint(beckn_api)

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True)
