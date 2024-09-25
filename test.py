from datetime import datetime
from flask import Flask, request
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://admin:LK3tT4mw1BZpstaG@cluster0.wpnwdpw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
app.config["MONGO_DBNAME"] = "expenseapp"  # Specify the database name
mongo = PyMongo(app)

def setup_mongo():
    try:
        client = mongo.cx  # Create a client instance
        db = client["expenseapp"]  # Access the database
        db.command("ping")
        print("MongoDB connection established")
    except Exception as e:
        print("Error establishing MongoDB connection:", e)

setup_mongo()  # Call the setup_mongo function once, when the application starts

@app.route('/expenses', methods=['POST'])
def add_expense():
    print("Request object:", request)
    data = request.get_json(force=True)
    print("Received data:", data)

    expense = {
        'title': data['title'],
        'amount': data['amount'],
        'category': data['category'],
        'date': datetime.utcnow(),
        'type': 'expense'
    }

    # Your code here
    pass

if __name__ == "__main__":
    app.run(debug=True)