from flask import Flask,redirect
from dotenv import load_dotenv
import os

from routes.auth import auth_bp
from routes.expense import expense_bp
from routes.group import group_bp
from routes.dashboard import dashboard_bp   
from routes.settle  import settle_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(auth_bp)
app.register_blueprint(expense_bp)
app.register_blueprint(group_bp)
app.register_blueprint(dashboard_bp) 
app.register_blueprint(settle_bp)

@app.route("/")
def root():
    return redirect("/login")  

if __name__ == "__main__":
    app.run(debug=True)
