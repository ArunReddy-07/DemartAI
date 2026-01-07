import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'data' / 'dmartai.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create inventory analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT,
            season TEXT NOT NULL,
            current_stock INTEGER NOT NULL,
            predicted_demand INTEGER,
            recommendation TEXT,
            decision TEXT,
            price REAL,
            unit TEXT,
            optimal_level INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create chatbot conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chatbot_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user activity table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_type TEXT NOT NULL,
            description TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create products table to persist product catalog
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            current_price REAL,
            unit TEXT,
            historical_price_avg REAL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create users table for basic user data storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT,
            role TEXT DEFAULT 'user',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")
    # Seed products from JSON if table is empty
    try:
        seed_products_from_json()
    except Exception as e:
        print(f"Failed to seed products: {e}")

def save_analysis(product_name, category, season, current_stock, prediction_result):
    """Save inventory analysis to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO inventory_analysis 
            (product_name, category, season, current_stock, predicted_demand, 
             recommendation, decision, price, unit, optimal_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_name,
            category,
            season,
            current_stock,
            prediction_result.get('predicted_demand'),
            prediction_result.get('recommendation', {}).get('advice', ''),
            prediction_result.get('recommendation', {}).get('decision', ''),
            prediction_result.get('price'),
            prediction_result.get('unit'),
            prediction_result.get('recommendation', {}).get('optimal_level'),
            datetime.now(),
            datetime.now()
        ))
        conn.commit()
        analysis_id = cursor.lastrowid
        conn.close()
        return analysis_id
    except Exception as e:
        conn.close()
        print(f"Error saving analysis: {e}")
        return None

def save_product(product_obj):
    """Insert or update a product in the products table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (name, category, current_price, unit, historical_price_avg, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                category=excluded.category,
                current_price=excluded.current_price,
                unit=excluded.unit,
                historical_price_avg=excluded.historical_price_avg,
                metadata=excluded.metadata,
                updated_at=excluded.updated_at
        ''', (
            product_obj.get('name'),
            product_obj.get('category'),
            product_obj.get('current_price'),
            product_obj.get('unit'),
            product_obj.get('historical_price_avg'),
            json.dumps(product_obj.get('metadata', {})),
            datetime.now()
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error saving product: {e}")
        return False

def get_all_products():
    """Return all products from the products table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name, category, current_price, unit, historical_price_avg, metadata FROM products ORDER BY name')
        rows = cursor.fetchall()
        products = []
        for r in rows:
            meta = r['metadata'] if r['metadata'] else '{}'
            try:
                meta_obj = json.loads(meta)
            except Exception:
                meta_obj = {}
            products.append({
                'name': r['name'],
                'category': r['category'],
                'current_price': r['current_price'],
                'unit': r['unit'],
                'historical_price_avg': r['historical_price_avg'],
                'metadata': meta_obj
            })
        conn.close()
        return products
    except Exception as e:
        conn.close()
        print(f"Error fetching products: {e}")
        return []

def seed_products_from_json():
    """Seed the products table from data/products.json if empty"""
    # Only import here to avoid circular imports at module load
    from pathlib import Path as _Path
    import json as _json

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as cnt FROM products')
    cnt = cursor.fetchone()['cnt']
    conn.close()

    if cnt > 0:
        return

    products_path = Path(__file__).parent / 'data' / 'products.json'
    if not products_path.exists():
        return

    with open(products_path, 'r', encoding='utf-8') as f:
        data = _json.load(f)

    for p in data:
        prod = {
            'name': p.get('name'),
            'category': p.get('category'),
            'current_price': p.get('current_price'),
            'unit': p.get('unit'),
            'historical_price_avg': p.get('historical_price_avg'),
            'metadata': {k: v for k, v in p.items() if k not in ['name', 'category', 'current_price', 'unit', 'historical_price_avg']}
        }
        try:
            save_product(prod)
        except Exception as e:
            print(f"Failed to insert product {prod.get('name')}: {e}")

def save_chat(user_message, bot_response, source='fallback'):
    """Save chatbot conversation to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO chatbot_conversations 
            (user_message, bot_response, source, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            user_message,
            bot_response,
            source,
            datetime.now()
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error saving chat: {e}")
        return False

def log_activity(activity_type, description, details=None):
    """Log user activity"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO user_activity 
            (activity_type, description, details, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            activity_type,
            description,
            details,
            datetime.now()
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error logging activity: {e}")
        return False

def get_analytics_data():
    """Get analytics data from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total analyses
        cursor.execute('SELECT COUNT(*) as count FROM inventory_analysis')
        total_analyses = cursor.fetchone()['count']
        
        # Category distribution
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM inventory_analysis 
            GROUP BY category
        ''')
        categories = dict(cursor.fetchall())
        
        # Seasonal distribution
        cursor.execute('''
            SELECT season, COUNT(*) as count 
            FROM inventory_analysis 
            GROUP BY season
        ''')
        seasons = dict(cursor.fetchall())
        
        # Decision distribution
        cursor.execute('''
            SELECT decision, COUNT(*) as count 
            FROM inventory_analysis 
            WHERE decision IS NOT NULL
            GROUP BY decision
        ''')
        decisions = dict(cursor.fetchall())
        
        # Top analyzed products
        cursor.execute('''
            SELECT product_name, COUNT(*) as count 
            FROM inventory_analysis 
            GROUP BY product_name 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_products = [dict(row) for row in cursor.fetchall()]
        
        # Recent analyses
        cursor.execute('''
            SELECT * FROM inventory_analysis 
            ORDER BY created_at DESC 
            LIMIT 20
        ''')
        recent_analyses = [dict(row) for row in cursor.fetchall()]
        
        # Chatbot stats
        cursor.execute('SELECT COUNT(*) as count FROM chatbot_conversations')
        total_chats = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM chatbot_conversations 
            GROUP BY source
        ''')
        chat_sources = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_analyses': total_analyses,
            'categories': categories,
            'seasons': seasons,
            'decisions': decisions,
            'top_products': top_products,
            'recent_analyses': recent_analyses,
            'total_chats': total_chats,
            'chat_sources': chat_sources
        }
    except Exception as e:
        conn.close()
        print(f"Error fetching analytics: {e}")
        return {}

def get_recent_analyses(limit=20):
    """Get recent inventory analyses"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM inventory_analysis 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        analyses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return analyses
    except Exception as e:
        conn.close()
        print(f"Error fetching recent analyses: {e}")
        return []

def get_product_history(product_name):
    """Get analysis history for a specific product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM inventory_analysis 
            WHERE product_name = ?
            ORDER BY created_at DESC
        ''', (product_name,))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
    except Exception as e:
        conn.close()
        print(f"Error fetching product history: {e}")
        return []
