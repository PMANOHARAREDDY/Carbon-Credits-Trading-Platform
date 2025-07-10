credits = []

def issue_credit(data):
    credit = {
        "credit_id": f"cc{len(credits)+1}",
        "project_id": data.get("project_id"),
        "amount": data.get("amount"),
        "owner": data.get("owner")
    }
    credits.append(credit)
    return {"status": "issued", "credit": credit}

def list_credits():
    return credits
