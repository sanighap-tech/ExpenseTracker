from flask import Flask, render_template, request, redirect,session,url_for
import matplotlib
matplotlib.use('Agg')   # Important for Flask
import matplotlib.pyplot as plt
import io
import base64
import json
import os


app = Flask(__name__, static_folder='static')
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

#app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session

# Dummy user (for learning)
USER_CREDENTIALS = {
    "admin": "1234"
}


# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_expenses():
    if not os.path.exists("expenses.json"):
        return []
    with open("expenses.json", "r") as file:
        return json.load(file)
    

# Save expenses
def save_expenses(expenses):
    with open("expenses.json", "w") as file:
        json.dump(expenses, file, indent=4)
        from flask import Flask, render_template, request, redirect, session, url_for

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session["user"] = username
            return redirect("/")
        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None

    if request.method == "POST":
        username = request.form["username"]
        new_password = request.form["new_password"]

        if username in USER_CREDENTIALS:
            USER_CREDENTIALS[username] = new_password
            message = "Password updated successfully!"
        else:
            message = "User not found!"

    return render_template("forgot_password.html", message=message)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# Protect Home Page
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    expenses = load_expenses()

    grouped_expenses = {}
    total_by_user = {}
    category_totals = {} 

    for exp in expenses:
        user = exp["user"]
        category = exp["category"]
        amount = float(exp["amount"])


        if user not in grouped_expenses:
            grouped_expenses[user] = []
            total_by_user[user] = 0

        grouped_expenses[user].append(exp)
        total_by_user[user] += amount
        if category not in category_totals:
            category_totals[category] = 0

        category_totals[category] += amount

    return render_template(
        "index.html",
        grouped_expenses=grouped_expenses,
        total_by_user=total_by_user,
        category_totals=category_totals
        
    )
    

@app.route("/add", methods=["POST"])
def add_expense():
    expenses = load_expenses()

    new_expense = {
        "user": request.form["user"],   # 👈 make sure form has name="user"
        "amount": request.form["amount"],
        "category": request.form["category"],
        "date": request.form["date"],
        "description": request.form["description"]
    }

    expenses.append(new_expense)
    save_expenses(expenses)

    return redirect("/")


# Upload JSON Route
@app.route("/upload", methods=["GET", "POST"])
def upload():

    grouped_uploaded = {}
    user_charts = {}   # 🔥 store chart per user

    if request.method == "POST":
        file = request.files["file"]

        if file and file.filename.endswith(".json"):
            data = json.load(file)

            # Step 1: Group expenses by user
            for exp in data:
                user = exp["user"]

                if user not in grouped_uploaded:
                    grouped_uploaded[user] = []

                grouped_uploaded[user].append(exp)

            # Step 2: Generate pie chart for EACH user
            for user, expenses in grouped_uploaded.items():

                category_totals = {}

                for exp in expenses:
                    category = exp["category"]
                    amount = float(exp["amount"])

                    if category not in category_totals:
                        category_totals[category] = 0

                    category_totals[category] += amount

                # Create pie chart
                if category_totals:
                    fig, ax = plt.subplots(figsize=(4, 4))

                    ax.pie(
                        category_totals.values(),
                        labels=category_totals.keys(),
                        autopct='%1.1f%%',
                        startangle=90
                    )

                    ax.set_title(f"{user}'s Expense Distribution")

                    img = io.BytesIO()
                    plt.savefig(img, format='png')
                    img.seek(0)

                    user_charts[user] = base64.b64encode(
                        img.getvalue()
                    ).decode()

                    plt.close(fig)

    return render_template(
        "upload.html",
        grouped_uploaded=grouped_uploaded,
        user_charts=user_charts   # 🔥 send this
    )
if __name__ == "__main__":
    app.run(debug=True)