import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import config
from models.predictor import InventoryPredictor
from database import (init_db, save_analysis, save_chat, log_activity, 
                      get_analytics_data, get_recent_analyses, get_product_history, get_all_products)
import google.generativeai as genai
from pathlib import Path
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])
app.secret_key = os.getenv('SECRET_KEY', 'dmart-secret-key-2026')

# Initialize predictor
predictor = InventoryPredictor()

# Initialize database
init_db()

# Configure Google Generative AI
api_key = app.config.get('GOOGLE_API_KEY', '').strip()
if api_key and api_key not in ['your-google-api-key-here', '']:
    try:
        genai.configure(api_key=api_key)
        print(f"✓ Google Gemini API configured successfully")
    except Exception as e:
        print(f"✗ Failed to configure Google Gemini API: {e}")
else:
    print(f"⚠ No valid Google Gemini API key found. Using fallback responses.")

def load_products():
    """Load products from JSON file"""
    # Prefer products stored in the database (persisted). Fall back to JSON file.
    try:
        products = get_all_products()
        if products:
            return products
    except Exception:
        pass

    products_path = Path(__file__).parent / 'data' / 'products.json'
    try:
        with open(products_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        return jsonify({'error': 'Invalid method'}), 405
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login"""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    # Demo credentials check
    if email == 'demo@dmart.com' and password == 'demo123':
        session['user_id'] = 'demo_user'
        session['email'] = email
        session['username'] = 'Demo User'
        return jsonify({'status': 'success', 'message': 'Logged in successfully'}), 200
    
    # Default fallback login (for demo purposes)
    if email and password:
        session['user_id'] = 'user_' + email.replace('@', '_').replace('.', '_')
        session['email'] = email
        session['username'] = email.split('@')[0].title()
        return jsonify({'status': 'success', 'message': 'Logged in successfully'}), 200
    
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/update-profile', methods=['POST'])
def api_update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    
    if not username or not email:
        return jsonify({'success': False, 'message': 'Username and email are required'}), 400
    
    # Update session
    session['username'] = username
    session['email'] = email
    
    log_activity('profile_update', f'User updated profile', f'{email}')
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'username': username,
        'email': email
    })

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page - Dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    products = load_products()
    log_activity('page_visit', 'User visited dashboard')
    return render_template('index.html', products=products)

@app.route('/analytics')
def analytics():
    """Analytics page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    log_activity('page_visit', 'User visited analytics page')
    return render_template('analytics.html')

@app.route('/settings')
def settings():
    """Settings page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    log_activity('page_visit', 'User visited settings page')
    return render_template('settings.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/products', methods=['GET'])
def api_get_products():
    """Get all products"""
    products = load_products()
    return jsonify(products)

@app.route('/api/dashboard-stats', methods=['GET'])
def api_dashboard_stats():
    """Get dashboard statistics"""
    products = load_products()
    # Calculate statistics
    total_products = len(products)
    categories = {}
    total_price = 0
    
    for product in products:
        category = product.get('category', 'Miscellaneous')
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
        total_price += product.get('current_price', 0)
    
    avg_price = round(total_price / total_products, 2) if total_products > 0 else 0
    analytics_data = get_analytics_data()

    stats = {
        'total_products': total_products,
        'total_analyses': analytics_data.get('total_analyses', 0),
        'total_chats': analytics_data.get('total_chats', 0),
        'categories': list(categories.keys()),
        'avg_price': f"₹{avg_price}",
        'low_stock_items': 0,
        'high_demand_items': 0,
        'category_distribution': categories
    }
    
    return jsonify(stats)

@app.route('/api/analytics-data', methods=['GET'])
def api_analytics_data():
    """Get detailed analytics data"""
    analytics_data = get_analytics_data()
    return jsonify(analytics_data)

@app.route('/api/recent-analyses', methods=['GET'])
def api_recent_analyses():
    """Get recent inventory analyses"""
    limit = request.args.get('limit', 20, type=int)
    analyses = get_recent_analyses(limit)
    return jsonify(analyses)

@app.route('/api/product-history/<product_name>', methods=['GET'])
def api_product_history(product_name):
    """Get analysis history for a product"""
    history = get_product_history(product_name)
    return jsonify(history)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Analyze product inventory"""
    data = request.get_json()
    if not all(key in data for key in ['product', 'season', 'stock']):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        stock = int(data['stock'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid stock value'}), 400

    # Get prediction
    prediction = predictor.predict_stock_requirement(
        data['product'],
        stock,
        data['season']
    )

    # Save to database
    try:
        save_analysis(
            data['product'],
            prediction.get('category'),
            data['season'],
            stock,
            prediction
        )
    except Exception as e:
        print(f"Failed to save analysis: {e}")

    # Log activity
    log_activity(
        'inventory_analysis',
        f'Analyzed {data["product"]} for {data["season"]} season',
        json.dumps({'stock': stock, 'decision': prediction.get('recommendation', {}).get('decision')})
    )

    return jsonify(prediction)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """AI Chatbot endpoint using Google Gemini"""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Empty message'}), 400
    
    try:
        # Check if API key is available and valid
        api_key = app.config.get('GOOGLE_API_KEY', '').strip()
        
        if api_key and api_key not in ['your-google-api-key-here', '', None]:
            try:
                # Prepare context for the AI
                products = load_products()
                categories = list(set(p.get('category', 'Miscellaneous') for p in products))
                
                system_prompt = f"""You are an expert AI assistant for D-Mart Smart Inventory Management System.
You help with:
- Inventory management and stock optimization
- Seasonal trends and demand forecasting
- Product pricing strategies
- Category insights: {', '.join(categories) if categories else 'General'}
- Best practices for retail management

Available product categories: {', '.join(categories) if categories else 'Various'}

Provide concise, actionable advice. Be professional but friendly. Keep responses to 2-3 sentences unless asked for more details."""
                
                print(f"[Chatbot] Calling Google Gemini API...")
                print(f"[Chatbot] Message: {message[:100]}")
                
                # Call Google Gemini API
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(
                    f"{system_prompt}\n\nUser: {message}",
                    generation_config={"temperature": 0.7, "max_output_tokens": 500}
                )
                
                # Extract text response
                if response and response.text:
                    answer = response.text.strip()
                else:
                    answer = str(response) if response else "No response from API"
                
                print(f"[Chatbot] API Response received: {len(answer)} chars")
                
                # Save to database
                try:
                    save_chat(message, answer, 'google-gemini')
                    log_activity('chatbot_interaction', 'AI response generated', message[:50])
                except Exception as e:
                    print(f"Failed to save chat: {e}")
                
                return jsonify({
                    'response': answer,
                    'status': 'success',
                    'source': 'google-gemini'
                })
            
            except Exception as api_error:
                print(f"[Chatbot] Google Gemini API Error: {str(api_error)}")
                print(f"[Chatbot] Falling back to keyword responses")
                # Fall through to fallback response
        
        # Use fallback response if API key not configured or API fails
        print(f"[Chatbot] Using fallback response for: {message[:50]}...")
        fallback_response = get_fallback_response(message)
        
        try:
            save_chat(message, fallback_response, 'fallback')
            log_activity('chatbot_interaction', 'Fallback response sent', message[:50])
        except Exception as e:
            print(f"Failed to save fallback chat: {e}")
        
        return jsonify({
            'response': fallback_response,
            'status': 'success',
            'source': 'fallback'
        })
    
    except Exception as e:
        print(f"[Chatbot] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Last resort fallback
        fallback_response = "I apologize for the technical difficulty. Please try asking your question again or contact support."
        
        try:
            save_chat(message, fallback_response, 'error')
        except:
            pass
        
        return jsonify({
            'response': fallback_response,
            'status': 'error',
            'source': 'error-fallback'
        }), 500

def get_fallback_response(query):
    """Provide fallback responses when AI API is unavailable"""
    query_lower = query.lower()
    
    # Extended fallback responses
    responses = {
        'seasonal trends dairy': "Dairy products have stable demand year-round with slight increases during winter months. Yogurt and flavored milk see higher demand in summer. Plan inventory considering festivals like Diwali and Holi.",
        'seasonal trends vegetable': "Vegetables follow strong seasonal patterns. Summer vegetables: tomatoes, cucumber, bell peppers peak. Winter: root vegetables, leafy greens dominate. Monsoon brings better shelf life for stored vegetables.",
        'seasonal trends fruit': "Fruits are highly seasonal. Mangoes: summer peak. Apples/grapes: winter. Monsoon: stone fruits, citrus. Plan sourcing 2-3 weeks ahead. Consider storage capacity.",
        'festival demand': "Festival seasons (Diwali, Holi, NewYear) see 1.5-2x demand increases. Stock special items 3 weeks before. Snacks and dry goods see highest demand. Plan bulk purchases.",
        'summer inventory': "Summer strategy: Stock beverages at 1.5x normal levels. Increase fruits/vegetables daily. Reduce dairy shelf life considerations. Push ice-cream and cold beverages. Monitor expiry dates closely.",
        'winter inventory': "Winter strategy: Increase dairy products. Stock warm beverages (tea, coffee). Promote bakery items. Increase storage for longer shelf-life items. Plan for holiday shopping rush.",
        'inventory management': "Best practices: Monitor reorder points closely. Maintain 20% safety stock. Track fast-moving items weekly. Implement FIFO. Use inventory management system. Regular stock audits.",
        'pricing strategy': "Peak season: maintain or increase prices slightly. Off-season: run promotions. Monitor competitor pricing. Bundle slow items. Use dynamic pricing for perishables. Plan seasonal discounts.",
        'demand forecast': "Use historical data from same season last year. Adjust for growth (5-10% annual). Consider local events and festivals. Track weather patterns. Update forecasts weekly.",
        'reorder point': "Calculate: (Average Daily Sales × Lead Time) + Safety Stock. Review monthly. Adjust for seasonality. Set alerts in system. Monitor supplier reliability.",
        'hello': "Hello! I'm your D-Mart AI Assistant. I can help with inventory management, seasonal planning, pricing strategies, and product insights. What would you like to know?",
        'hi': "Hi there! Ask me about inventory optimization, seasonal trends, pricing, or product categories. How can I help today?",
        'help': "I can assist with: inventory management, seasonal demand forecasting, pricing strategies, category insights, stock optimization, and retail best practices. What's your question?",
    }
    
    # Check for exact matches first
    for key, response in responses.items():
        if key in query_lower:
            return response
    
    # Check for partial matches
    keywords = {
        'dairy': "Dairy products are staple items with consistent demand. Winter sees 1.3x demand. Consider storage capacity and shelf life.",
        'vegetable': "Vegetables are seasonal. Fresh sourcing critical. Monsoon: 1.0x. Summer: 1.3x. Winter: 1.2x demand.",
        'beverage': "Beverages peak in summer (1.5x demand). Winter demand drops. Keep cold drinks well-stocked in summer.",
        'season': "Seasons significantly impact inventory. Summer: beverages, fruits up. Winter: dairy, bakery up. Monsoon: groceries up.",
        'price': "Pricing depends on seasonality and demand. Peak season: maintain/increase. Off-season: promote. Monitor costs.",
        'stock': "Monitor stock levels closely. Set reorder points based on demand. Keep safety stock at 20%.",
        'forecast': "Demand forecasting uses historical data, seasonality, and growth projections. Update weekly.",
    }
    
    for keyword, response in keywords.items():
        if keyword in query_lower:
            return response
    
    return "I'd be happy to help! Ask me about inventory management, seasonal trends, pricing strategies, demand forecasting, or product categories. For real-time AI responses, please configure a Google Gemini API key in the .env file."

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== APP INITIALIZATION ====================

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8000)),
        debug=app.config['DEBUG']
    )
