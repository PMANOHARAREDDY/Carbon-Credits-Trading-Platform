import os
import json
from flask import Flask, redirect, session, request, jsonify
from flask_cors import CORS
from google_auth_oauthlib.flow import Flow
import requests
from datetime import datetime

BOARD_EMAIL = "manoharareddyp97@gmail.com"

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)

with open("client_secret.json") as f:
    oauth_config = json.load(f)

projects = []
credits = []

def find_project(project_id):
    for project in projects:
        if project["project_id"] == project_id:
            return project
    return None

def find_credit(credit_id):
    for credit in credits:
        if credit["credit_id"] == credit_id:
            return credit
    return None

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
    projects.append(project)
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
    return jsonify({"status": "verified", "project_id": project_id})

@app.route('/projects', methods=['GET'])
def get_all_projects():
    return jsonify(projects)

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
        "credit_id": f"cc{len(credits)+1}",
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
    credits.append(credit)
    return jsonify({"status": "issued", "credit": credit})

@app.route('/list_credits', methods=['GET'])
def list_all():
    user_email = request.args.get("user_email")
    is_board = user_email == BOARD_EMAIL
    if is_board:
        # Show all credits including blocked ones to board
        return jsonify(credits)
    if user_email:
        # Return all credits owned by the user, including blocked status info
        return jsonify([c for c in credits if c["owner_email"] == user_email])
    # For others, only credits that are for sale, not blocked, and verified
    return jsonify([c for c in credits if c["for_sale"] and not c["blocked"] and c["status"] == "verified"])

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
    return jsonify({"status": "released", "credit": credit})

@app.route('/board/projectwise_credits', methods=['GET'])
def board_projectwise_credits():
    projectwise = []
    for project in projects:
        project_credits = [c for c in credits if c["project_id"] == project["project_id"]]
        project_dict = dict(project)
        credits_list = [dict(c) for c in project_credits]
        projectwise.append({
            "project": project_dict,
            "credits": credits_list
        })
    return jsonify(projectwise)

@app.route('/board/creditwise_history', methods=['GET'])
def board_creditwise_history():
    return jsonify(credits)

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

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True)
