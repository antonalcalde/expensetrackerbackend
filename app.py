from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration for MongoDB
app.config['MONGO_URI'] = 'mongodb+srv://anton:1Ve9Qv9nNyFtDnRe@cluster0.wpnwdpw.mongodb.net/expenseapp?retryWrites=true&w=majority'
mongo = PyMongo(app)


# Utility function to convert MongoDB documents to JSON
def mongo_to_json(mongo_cursor):
    return [doc for doc in mongo_cursor]

# Routes
@app.route('/categories', methods=['GET'])
def get_categories():
    # assume this is your MongoDB collection
    collection = mongo.db.categories

    # fetch the categories from the database
    data = collection.find()

    # convert the ObjectId to a string or use a custom JSON encoder
    json_data = [{'_id': str(doc['_id']), **doc} for doc in data]

    # or use the bson library to serialize the ObjectId
    # json_data = json_util.dumps(data)

    # or use a custom JSON encoder
    # class CustomJSONEncoder(json.JSONEncoder):
    #     def default(self, obj):
    #         if isinstance(obj, ObjectId):
    #             return str(obj)
    #         return json.JSONEncoder.default(self, obj)
    # json_data = json.dumps(data, cls=CustomJSONEncoder)

    return jsonify(json_data)

# @app.route('/expenses', methods=['GET'])
# def get_expenses():
#     category = request.args.get('category')
#     query = {'category': category} if category else {}
#     expenses = mongo.db.data.find({'type': 'expense', **query})
#     return jsonify(mongo_to_json(expenses))


@app.route('/expenses', methods=['GET'])
def get_all_expenses():
    # Fetch all expenses from MongoDB
    expenses_cursor = mongo.db.data.find({'type': 'expense'})

    # Convert the Cursor to a list
    expenses_list = list(expenses_cursor)

    # Convert expenses to a list of dictionaries
    expenses = [{'id': str(expense['_id']), 'title': expense['title'], 'amount': expense['amount'], 'category': expense['category'], 'date': expense['date']} for expense in expenses_list]

    # Return the expenses as a JSON response
    return jsonify({'expenses': expenses})

@app.route('/expenses', methods=['POST'])
def add_expense():
    print("Request data:", request.data)  # Add this line
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data found'}), 400
        
        print("Received data:", data)
        
        expense = {
            'title': data['title'],
            'amount': data['amount'],
            'category': data['category'],
            'date': datetime.utcnow(),
            'type': 'expense'
        }

        result = mongo.db.data.insert_one(expense)
        print("Insert result:", result)
        
        if result.acknowledged:
            return jsonify({'id': str(result.inserted_id)}), 201
        else:
            return jsonify({'error': 'Failed to insert expense'}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/expenses/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        expense = mongo.db.data.find_one_and_delete({'_id': ObjectId(expense_id), 'type': 'expense'})
        if not expense:
            return jsonify({'message': 'Expense not found'}), 404

        # Update category
        mongo.db.data.update_one(
            {'type': 'category', 'title': expense['category']},
            {'$inc': {'entries': -1, 'total_amount': -expense['amount']}}
        )

        return jsonify({'message': 'Expense deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/expenses/total', methods=['GET'])
def get_total_expenses():
    # Fetch total expenses from MongoDB
    print("Received GET request to get total expenses")
    total_expenses_cursor = mongo.db.data.aggregate([
        {'$match': {'type': 'expense'}},
        {'$group': {'_id': None, 'totalExpenses': {'$sum': '$amount'}}}
    ])

    # Convert the CommandCursor to a list
    total_expenses_list = list(total_expenses_cursor)

    # Extract the total expenses value
    if not total_expenses_list:
        total_expenses = 0
    else:
        total_expenses = total_expenses_list[0]['totalExpenses']

    # Fetch categories from MongoDB
    categories_cursor = mongo.db.data.aggregate([
        {'$match': {'type': 'expense'}},
        {'$group': {'_id': '$category', 'totalAmount': {'$sum': '$amount'}}}
    ])

    # Convert the CommandCursor to a list
    categories_list = list(categories_cursor)

    # Convert categories to a list of dictionaries
    categories = [{'title': category['_id'], 'totalAmount': category['totalAmount']} for category in categories_list]

    # Return the total expenses and categories as a JSON response
    return jsonify({'totalExpenses': float(total_expenses), 'categories': categories}), 200, {'Content-Type': 'application/json'}

@app.route('/expenses/daily', methods=['GET'])
def calculate_daily_expenses():
    year = int(request.args.get('year'))
    month = int(request.args.get('month'))
    day = int(request.args.get('day'))
    start_date = datetime(year, month, day)
    end_date = start_date + timedelta(days=1)

    total_amount = mongo.db.data.aggregate([
        {'$match': {'date': {'$gte': start_date, '$lt': end_date}, 'type': 'expense'}},
        {'$group': {'_id': None, 'totalAmount': {'$sum': {'$toDouble': '$amount'}}}}
    ])
    
    result = list(total_amount)
    total_amount = result[0]['totalAmount'] if result else 0.0
    return jsonify({'totalAmount': total_amount})

@app.route('/expenses/weekly', methods=['GET'])
def calculate_weekly_expenses():
    start_date = datetime.fromisoformat(request.args.get('startDate'))
    end_date = datetime.fromisoformat(request.args.get('endDate'))

    total_amount = mongo.db.data.aggregate([
        {'$match': {'date': {'$gte': start_date, '$lte': end_date}, 'type': 'expense'}},
        {'$group': {'_id': None, 'totalAmount': {'$sum': {'$toDouble': '$amount'}}}}
    ])
    
    result = list(total_amount)
    total_amount = result[0]['totalAmount'] if result else 0.0
    return jsonify({'totalAmount': total_amount})

@app.route('/expenses/monthly', methods=['GET'])
def calculate_monthly_expenses():
    year = int(request.args.get('year'))
    month = int(request.args.get('month'))

    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1)

    total_amount = mongo.db.data.aggregate([
        {'$match': {'date': {'$gte': start_date, '$lt': end_date}, 'type': 'expense'}},
        {'$group': {'_id': None, 'totalAmount': {'$sum': {'$toDouble': '$amount'}}}}
    ])
    
    result = list(total_amount)
    total_amount = result[0]['totalAmount'] if result else 0.0
    return jsonify({'totalAmount': total_amount})

@app.route('/expenses/yearly', methods=['GET'])
def calculate_yearly_expenses():
    year = int(request.args.get('year'))

    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)

    total_amount = mongo.db.data.aggregate([
        {'$match': {'date': {'$gte': start_date, '$lt': end_date}, 'type': 'expense'}},
        {'$group': {'_id': None, 'totalAmount': {'$sum': {'$toDouble': '$amount'}}}}
    ])
    
    result = list(total_amount)
    total_amount = result[0]['totalAmount'] if result else 0.0
    return jsonify({'totalAmount': total_amount})

@app.route('/incomes', methods=['GET'])
def get_incomes():
    incomes = mongo.db.data.find({'type': 'income'})
    return jsonify(mongo_to_json(incomes))

@app.route('/incomes', methods=['POST'])
def add_income():
    data = request.json
    income = {
        'title': data['title'],
        'amount': data['amount'],
        'type': 'income'
    }
    try:
        result = mongo.db.data.insert_one(income)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/incomes/<income_id>', methods=['DELETE'])
def delete_income(income_id):
    try:
        result = mongo.db.data.find_one_and_delete({'_id': ObjectId(income_id), 'type': 'income'})
        if not result:
            return jsonify({'message': 'Income not found'}), 404

        return jsonify({'message': 'Income deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
