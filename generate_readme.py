import os

base_dir = r"C:\Users\praka\.gemini\antigravity\scratch\nutrisense"
output_file = os.path.join(base_dir, "NutriSense_Master_README.md")

files_to_include = [
    ("backend/app.py", "python"),
    ("backend/utils.py", "python"),
    ("backend/food_data.py", "python"),
    ("backend/firebase_service.py", "python"),
    ("backend/requirements.txt", "text"),
    ("frontend/package.json", "json"),
    ("frontend/vite.config.js", "javascript"),
    ("frontend/index.html", "html"),
    ("frontend/src/main.jsx", "javascript"),
    ("frontend/src/App.jsx", "javascript"),
    ("frontend/src/index.css", "css"),
    ("frontend/src/api/client.js", "javascript"),
    ("frontend/src/pages/Dashboard.jsx", "javascript"),
    ("frontend/src/pages/AddMeal.jsx", "javascript")
]

# Ensure backend/requirements.txt exists
req_path = os.path.join(base_dir, "backend", "requirements.txt")
os.makedirs(os.path.dirname(req_path), exist_ok=True)
with open(req_path, "w", encoding="utf-8") as f:
    f.write("flask\nflask-cors\nfirebase-admin\nrequests\n")

# Make sure frontend/src/firebase_config.js exists as a template just in case
template_path = os.path.join(base_dir, "frontend", "src", "firebase_config.js")
if not os.path.exists(template_path):
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    with open(template_path, "w", encoding="utf-8") as f:
        f.write("// firebase_config.js\n// Add your config here")

readme_content = """# NutriSense - Master Project Document

This document contains EVERYTHING required to recreate the NutriSense full-stack application from scratch.

---

# 📁 SECTION 1 — PROJECT STRUCTURE

```text
nutrisense/
├── backend/
│   ├── app.py
│   ├── utils.py
│   ├── food_data.py
│   ├── firebase_service.py
│   ├── requirements.txt
│   └── serviceAccountKey.json (placeholder)
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── firebase_config.js (placeholder)
│       ├── api/
│       │   └── client.js
│       └── pages/
│           ├── Dashboard.jsx
│           └── AddMeal.jsx
```

---

# 📦 SECTION 2 — FULL CODE

"""

for filepath, lang in files_to_include:
    full_path = os.path.join(base_dir, filepath)
    readme_content += f"## filename: {filepath}\n\n```{lang}\n"
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            readme_content += f.read()
    else:
        readme_content += "// File missing or not created yet."
    readme_content += "\n```\n\n"

readme_content += """---

# ⚙️ SECTION 3 — REQUIREMENTS

## Python dependencies (requirements.txt)
```text
flask
flask-cors
firebase-admin
requests
```

## Node dependencies (package.json)
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "firebase": "^10.7.0",
    "lucide-react": "^0.300.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "recharts": "^2.10.3"
  }
}
```

---

# 🔐 SECTION 4 — FIREBASE SETUP

1. **Create Firebase Project:** Go to the Firebase Console and create a new project.
2. **Enable Firestore:** Navigate to Firestore Database and click "Create Database".
3. **Enable Authentication:** Go to Authentication > Sign-in method, and enable Email/Password.
4. **Download serviceAccountKey.json:** Go to Project Settings > Service Accounts > Generate new private key.
5. **Place in backend/:** Save the downloaded JSON file as `backend/serviceAccountKey.json`.
6. **Add frontend firebase config:** Copy your web app config from Firebase settings and place it in `frontend/src/firebase_config.js`.

---

# 🚀 SECTION 5 — RUN INSTRUCTIONS

## Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

## Frontend
```bash
cd frontend
npm install
npm run dev
```

---

# 🧪 SECTION 6 — TESTING

Sample API request for `/analyze-meal`:

```json
{
  "foods": [
    {"food": "idli", "quantity": 3, "unit": "piece"},
    {"food": "sambar", "quantity": 1, "unit": "cup"}
  ]
}
```
"""

with open(output_file, "w", encoding="utf-8") as f:
    f.write(readme_content)

print(f"Master README created successfully at {output_file}")
