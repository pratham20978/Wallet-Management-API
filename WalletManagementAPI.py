#!/usr/bin/env python3

from flask import Flask, request, jsonify
from authenticator import Authenticator
from collections import defaultdict
from datetime import datetime
from functools import wraps

app = Flask(__name__)
authenticator = Authenticator(credentials_file = "user.txt", secret_key="your_secret_key")


#Define authentication middleware
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error':'Token is missing'}),401
        
        username = authenticator.validate_token(token)
        if not username:
            return jsonify({'error':'Invalid token'}),401
        return f(*args,**kwargs)
    return decorated_function


class Auth:
    
    @app.route('/api/auth/signup', methods =['POST'])
    def signup():
        data = request.json

        # Validation
        if not all(key in data for key in ('username', 'email', 'password')):
            return jsonify({'error':'Missing credentials'}),400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        success, message = authenticator.register_user(username, email,password)
        if success:
            return jsonify({'message':message}),201
        else:
            return jsonify({'error': message}), 400

    @app.route('/api/auth/login', methods = ['POST'])
    def login():
        data = request.json

        #validation
        if not all(key in data for key in ('username', 'password')):
            return jsonify({'error':'Missing Credentials'}),400

        username = data.get('username')
        password = data.get('password')

        success, token_or_message = authenticator.login(username, password)
        if success:
            return jsonify({'token': token_or_message}), 200
        else:
            return jsonify({'error': token_or_message}), 401
        


class Expense_Management:
    
    # Dumm data to simpulate user expenses
    
    user_expenses=[]
    
    @app.route('/api/expenses', methods=['POST'])
    @token_required
    def add_expenses():
        
        # Get expensed data from request body
        data = request.json
    
        # Validation
        if not all(key in data for key in ('title', 'date','amount', 'category')):
            return jsonify({'error': 'Missing required field'}),400
    
    
        title = data.get('title')
        date = data.get('date')
        amount = data.get('amount')
        category = data.get('category')
    
        # Add expense to the list
        user_expenses.append({
            'title':title, 'date':date, 'amount':amount, 'category':category
        })
    
        return jsonify({'message':'Expense added succesfully'}), 201
    

    @app.route('/api/expenses', methods = ['GET'])
    @token_required
    def get_expenses():
        
        # Paginate expenses eg 10 expenses per page
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        start_index = (page-1)* per_page
        end_index = start_index + per_page

        paginated_expenses = user_expenses[start_index:end_index]
    
        return jsonify({'exepenes': paginated_expenses}),200
    
    
    @app.route('/api/expenses/grouped', methods=['GET'])
    @token_required
    def get_grouped_expenses():
       
        grouped_expenses = defaultdict(list)
        for expenses in user_expenses:
            grouped_expenses[expenses['category']].append(expenses)
    
        # optinonllay filer by month
        month = request.args.get('month')
        if month:
            filtered_expenses = {}
            for category, expenses in grouped_expenses.items():
                filtered_expenses[category]= [expense for expense in expenses if expense['data'].startswith(month)]
            grouped_expenses = filtered_expenses
    
        return jsonify({'grouped_expenses': dict(grouped_expenses)}),200
    
    @app.route('/api/expenses/<int:category_id>/monthly')
    @token_required
    def get_monthly_expenses(category_id):
        
        category_exepenses = [expense for expense in user_expenses if expense['category']==category_id]
    
        monthly_expenses = defaultdict(lambda:defaultdict(int))
        for expense in category_exepenses:
            date = datetime.strptime(expense['date'], '%Y-%m-%d')
            month = date.strftime('%Y-%m')
            day=date.day
            monthly_expenses[month][day] += expense['amount']
    
        return jsonify({'monthly_expenses': dict(monthly_expenses)}),200
    

class Expense_Categories_Management:
   
    expense_categories = []
    
    @app.route('/api/categoies', methods=['GET'])
    @token_required
    def get_categories():
        
        return jsonify({'categories': expense_categories}), 200
    

    @app.route('/api/categories', methods=['POST'])
    @token_required
    def add_category():
        
        # Get category data from request body
        data = request.json
        category_name = data.get('name')
    
        # add category to list
        expense_categories.append(category_name)
    
        return jsonify({'message': 'Category added succesfully'}), 201
    

    @app.route('/api/categories/<int:category_id>', methods=['DELETE'])
    @token_required
    def delete_category(categroy_id):
        
        # check if category_id is valid
        if categroy_id < 0 or categroy_id >=len(expense_categories):
            return jsonify({'error': 'Invalid category ID'}), 400
        
        # Delete category
        del expense_categories[categroy_id]
    
        return jsonify({'message': 'Category delete successfully'}), 200
    
    