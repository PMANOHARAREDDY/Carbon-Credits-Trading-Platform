from flask import Blueprint, request, jsonify, current_app

beckn_api = Blueprint('beckn_api', __name__)

def credit_to_beckn_item(credit):
    return {
        "id": credit["id"],
        "descriptor": {"name": f"Credit {credit['id']}"},
        "tags": [
            {"code": "project_id", "value": credit["project_id"]},
            {"code": "owner", "value": credit["owner"]},
            {"code": "status", "value": credit["status"]},
        ]
    }

@beckn_api.route('/beckn/search', methods=['POST'])
def beckn_search():
    credits = current_app.config['CREDITS']
    available_credits = [c for c in credits if c['status'] == 'active']
    items = [credit_to_beckn_item(c) for c in available_credits]
    return jsonify({"message": "Beckn search", "items": items})

@beckn_api.route('/beckn/select', methods=['POST'])
def beckn_select():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['id'] == credit_id), None)
    if not credit or credit['status'] != 'active':
        return jsonify({"error": "Credit not available"}), 404
    return jsonify({"message": "Credit selected", "item": credit_to_beckn_item(credit)})

@beckn_api.route('/beckn/init', methods=['POST'])
def beckn_init():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['id'] == credit_id), None)
    if not credit or credit['status'] != 'active':
        return jsonify({"error": "Credit not available"}), 404
    return jsonify({"message": "Transaction initialized", "item": credit_to_beckn_item(credit)})

@beckn_api.route('/beckn/confirm', methods=['POST'])
def beckn_confirm():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    buyer = data.get("buyer", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['id'] == credit_id), None)
    if not credit or credit['status'] != 'active':
        return jsonify({"error": "Credit not available"}), 404
    credit['owner'] = buyer
    credit['history'].append({"owner": buyer, "action": "beckn_transfer"})
    return jsonify({"message": "Transaction confirmed", "item": credit_to_beckn_item(credit)})

@beckn_api.route('/beckn/status', methods=['POST'])
def beckn_status():
    data = request.json
    credit_id = data.get("item", {}).get("id")
    credits = current_app.config['CREDITS']
    credit = next((c for c in credits if c['id'] == credit_id), None)
    if not credit:
        return jsonify({"error": "Credit not found"}), 404
    return jsonify({"item": credit_to_beckn_item(credit), "history": credit.get("history", [])})
