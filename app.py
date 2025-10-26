"""
Azure Expense Tracker - Complete Flask Web Application
Track your expenses with Azure Blob Storage and Cosmos DB
"""

import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Initialize Azure Blob Storage
blob_service = BlobServiceClient.from_connection_string(
    os.getenv('AZURE_STORAGE_CONNECTION_STRING')
)
container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')

# Initialize Azure Cosmos DB
cosmos_client = CosmosClient(
    os.getenv('COSMOS_ENDPOINT'),
    os.getenv('COSMOS_KEY')
)
database = cosmos_client.get_database_client(os.getenv('COSMOS_DATABASE_NAME'))
container = database.get_container_client(os.getenv('COSMOS_CONTAINER_NAME'))


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# HTML TEMPLATES
# ============================================================

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expense Tracker Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 36px;
        }
        .subtitle { color: #666; font-size: 16px; }
        .nav {
            margin-top: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .nav a {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 8px;
            display: inline-block;
            transition: all 0.3s;
            font-weight: 500;
        }
        .nav a:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 {
            color: #667eea;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #333;
        }
        .stat-label {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        .content-box {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .content-box h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 24px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f8f9fa;
            color: #667eea;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
        }
        tbody tr { transition: background 0.2s; }
        tbody tr:hover { background: #f8f9fa; }
        .amount {
            font-weight: bold;
            color: #e74c3c;
            font-size: 16px;
        }
        .category-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background: #667eea;
            color: white;
        }
        .btn-delete {
            background: #e74c3c;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s;
        }
        .btn-delete:hover {
            background: #c0392b;
            transform: scale(1.05);
        }
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            animation: slideIn 0.3s;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state h3 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #666;
        }
        .category-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .category-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.2s;
        }
        .category-item:hover {
            transform: translateX(5px);
            background: #e9ecef;
        }
        @media (max-width: 768px) {
            .stats { grid-template-columns: 1fr; }
            h1 { font-size: 24px; }
            table { font-size: 12px; }
            th, td { padding: 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>💰 Azure Expense Tracker</h1>
            <p class="subtitle">Track and manage your expenses with Azure Cloud</p>
            <div class="nav">
                <a href="/">📊 Dashboard</a>
                <a href="/add">➕ Add Expense</a>
                <a href="/expenses">📋 All Expenses</a>
            </div>
        </header>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="stats">
            <div class="stat-card">
                <h3>Total Expenses</h3>
                <div class="stat-value">₹{{ "%.2f"|format(total) }}</div>
                <div class="stat-label">All time</div>
            </div>
            <div class="stat-card">
                <h3>This Month</h3>
                <div class="stat-value">₹{{ "%.2f"|format(month_total) }}</div>
                <div class="stat-label">{{ current_month }}</div>
            </div>
            <div class="stat-card">
                <h3>Total Records</h3>
                <div class="stat-value">{{ count }}</div>
                <div class="stat-label">Transactions</div>
            </div>
            <div class="stat-card">
                <h3>Categories</h3>
                <div class="stat-value">{{ categories_count }}</div>
                <div class="stat-label">Active</div>
            </div>
        </div>

        {% if category_totals %}
        <div class="content-box">
            <h2>💳 Expenses by Category</h2>
            <div class="category-list">
                {% for cat in category_totals %}
                <div class="category-item">
                    <span class="category-badge">{{ cat.category }}</span>
                    <span class="amount">₹{{ "%.2f"|format(cat.total) }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <div class="content-box">
            <h2>📝 Recent Expenses</h2>
            {% if expenses %}
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Merchant</th>
                            <th>Category</th>
                            <th>Amount</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for exp in expenses %}
                        <tr>
                            <td>{{ exp.date }}</td>
                            <td><strong>{{ exp.description }}</strong></td>
                            <td>{{ exp.merchant or '-' }}</td>
                            <td><span class="category-badge">{{ exp.category }}</span></td>
                            <td class="amount">₹{{ "%.2f"|format(exp.amount) }}</td>
                            <td>
                                <form method="POST" action="/delete/{{ exp.id }}/{{ exp.category }}" style="display: inline;">
                                    <button type="submit" class="btn-delete" onclick="return confirm('Delete this expense?')">🗑️ Delete</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <div class="empty-state">
                    <h3>📭 No expenses yet</h3>
                    <p>Click "Add Expense" to start tracking!</p>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

ADD_EXPENSE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Expense</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .card {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .back-link {
            display: inline-block;
            color: #667eea;
            margin-bottom: 20px;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }
        .back-link:hover { color: #5568d3; }
        .form-group { margin-bottom: 25px; }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }
        .required { color: #e74c3c; }
        input, select, textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        select { cursor: pointer; }
        .btn-submit {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
        }
        .btn-submit:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        .file-label {
            display: block;
            padding: 12px 15px;
            border: 2px dashed #e0e0e0;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            color: #666;
        }
        .file-label:hover {
            border-color: #667eea;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>➕ Add New Expense</h1>
            <p style="color: #666; margin-bottom: 30px;">Enter your expense details</p>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Amount <span class="required">*</span></label>
                    <input type="number" name="amount" step="0.01" min="0" required placeholder="₹ 0.00">
                </div>

                <div class="form-group">
                    <label>Category <span class="required">*</span></label>
                    <select name="category" required>
                        <option value="">Select category...</option>
                        <option value="Food">🍔 Food & Dining</option>
                        <option value="Transport">🚗 Transport</option>
                        <option value="Shopping">🛍️ Shopping</option>
                        <option value="Bills">💡 Bills & Utilities</option>
                        <option value="Entertainment">🎬 Entertainment</option>
                        <option value="Healthcare">🏥 Healthcare</option>
                        <option value="Education">📚 Education</option>
                        <option value="Travel">✈️ Travel</option>
                        <option value="Other">📦 Other</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Description <span class="required">*</span></label>
                    <input type="text" name="description" required placeholder="e.g., Lunch at restaurant">
                </div>

                <div class="form-group">
                    <label>Merchant / Vendor</label>
                    <input type="text" name="merchant" placeholder="e.g., McDonald's">
                </div>

                <div class="form-group">
                    <label>Date <span class="required">*</span></label>
                    <input type="date" name="date" value="{{ today }}" required>
                </div>

                <div class="form-group">
                    <label>Receipt (Optional)</label>
                    <label class="file-label" for="receipt">
                        📎 Click to upload receipt (PDF, JPG, PNG)
                    </label>
                    <input type="file" name="receipt" id="receipt" accept=".pdf,.jpg,.jpeg,.png,.gif" style="display:none;">
                </div>

                <button type="submit" class="btn-submit">💾 Save Expense</button>
            </form>
        </div>
    </div>

    <script>
        document.getElementById('receipt').addEventListener('change', function(e) {
            var label = document.querySelector('.file-label');
            var fileName = e.target.files[0] ? e.target.files[0].name : '📎 Click to upload receipt';
            label.textContent = fileName;
        });
    </script>
</body>
</html>
"""

EXPENSES_LIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Expenses</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        h1 { color: #667eea; font-size: 32px; }
        .back-link {
            display: inline-block;
            color: #667eea;
            margin-bottom: 15px;
            text-decoration: none;
            font-weight: 500;
        }
        .content-box {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f8f9fa;
            color: #667eea;
            font-weight: 600;
        }
        tr:hover { background: #f8f9fa; }
        .amount {
            font-weight: bold;
            color: #e74c3c;
        }
        .category-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background: #667eea;
            color: white;
        }
        .btn-delete {
            background: #e74c3c;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        .btn-delete:hover { background: #c0392b; }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>📋 All Expenses</h1>
            <p style="color: #666; margin-top: 10px;">Total: {{ expenses|length }} expenses</p>
        </header>

        <div class="content-box">
            {% if expenses %}
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Merchant</th>
                            <th>Category</th>
                            <th>Amount</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for exp in expenses %}
                        <tr>
                            <td>{{ exp.date }}</td>
                            <td><strong>{{ exp.description }}</strong></td>
                            <td>{{ exp.merchant or '-' }}</td>
                            <td><span class="category-badge">{{ exp.category }}</span></td>
                            <td class="amount">₹{{ "%.2f"|format(exp.amount) }}</td>
                            <td>
                                <form method="POST" action="/delete/{{ exp.id }}/{{ exp.category }}" style="display: inline;">
                                    <button type="submit" class="btn-delete" onclick="return confirm('Delete?')">Delete</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <div class="empty-state">
                    <h3>No expenses found</h3>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    """Dashboard - Main page"""
    try:
        # Get all expenses
        query = "SELECT * FROM c ORDER BY c.date DESC"
        expenses = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Calculate totals
        total = sum(exp.get('amount', 0) for exp in expenses)
        
        # This month's total
        current_month = datetime.now().strftime('%Y-%m')
        month_total = sum(exp.get('amount', 0) for exp in expenses 
                         if exp.get('date', '').startswith(current_month))
        
        # Category totals
        categories = {}
        for exp in expenses:
            cat = exp.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + exp.get('amount', 0)
        
        category_totals = [{'category': k, 'total': v} for k, v in categories.items()]
        
        return render_template_string(INDEX_TEMPLATE, 
                                     expenses=expenses[:10],
                                     total=total,
                                     month_total=month_total,
                                     current_month=datetime.now().strftime('%B %Y'),
                                     count=len(expenses),
                                     categories_count=len(categories),
                                     category_totals=category_totals)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template_string(INDEX_TEMPLATE, expenses=[], total=0, 
                                     month_total=0, current_month='', count=0,
                                     categories_count=0, category_totals=[])


@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    """Add new expense"""
    if request.method == 'POST':
        try:
            # Get form data
            amount = float(request.form.get('amount'))
            category = request.form.get('category')
            description = request.form.get('description')
            merchant = request.form.get('merchant', '')
            date = request.form.get('date')
            
            # Handle file upload
            receipt_url = None
            file = request.files.get('receipt')
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                blob_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                
                blob_client = blob_service.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )
                blob_client.upload_blob(file, overwrite=True)
                receipt_url = blob_client.url
            
            # Create expense
            expense = {
                'id': f"exp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                'amount': amount,
                'category': category,
                'description': description,
                'merchant': merchant,
                'date': date,
                'receipt_url': receipt_url,
                'created_at': datetime.now().isoformat()
            }
            
            container.create_item(body=expense)
            
            flash('✅ Expense added successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'❌ Error: {str(e)}', 'error')
    
    return render_template_string(ADD_EXPENSE_TEMPLATE, 
                                 today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/expenses')
def list_expenses():
    """List all expenses"""
    try:
        query = "SELECT * FROM c ORDER BY c.date DESC"
        expenses = list(container.query_items(query=query, enable_cross_partition_query=True))
        return render_template_string(EXPENSES_LIST_TEMPLATE, expenses=expenses)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template_string(EXPENSES_LIST_TEMPLATE, expenses=[])


@app.route('/delete/<expense_id>/<category>', methods=['POST'])
def delete_expense(expense_id, category):
    """Delete an expense"""
    try:
        container.delete_item(item=expense_id, partition_key=category)
        flash('✅ Expense deleted successfully!', 'success')
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
    
    return redirect(url_for('index'))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 AZURE EXPENSE TRACKER")
    print("=" * 60)
    print("Starting Flask application...")
    print("\n📍 Access the app at: http://localhost:5000")
    print("📍 Or: http://127.0.0.1:5000")
    print("\n⏹️  Press CTRL+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
