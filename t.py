from pymongo import MongoClient

client = MongoClient('mongodb+srv://anton:1Ve9Qv9nNyFtDnRe@cluster0.wpnwdpw.mongodb.net/myDatabase?retryWrites=true&w=majority')
db = client.expenseapp # Replace with your actual database name
print(db.list_collection_names())  # Should print the collection names
