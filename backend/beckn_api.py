# backend/beckn_api.py

projects = []

def register_project(data):
    project = {
        "project_id": f"proj{len(projects)+1}",
        "name": data.get("name"),
        "status": "registered"
    }
    projects.append(project)
    return {"status": "success", "project_id": project["project_id"]}

def verify_project(data):
    for project in projects:
        if project["project_id"] == data.get("project_id"):
            project["status"] = "verified"
            return {"status": "verified", "project_id": project["project_id"]}
    return {"status": "not found"}

def get_projects():
    return projects
