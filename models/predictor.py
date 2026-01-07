import json
import numpy as np
import pandas as pd
from pathlib import Path

class InventoryPredictor:
    """AI-powered inventory prediction model"""
    
    def __init__(self):
        self.seasonal_patterns = self._load_seasonal_patterns()
        self.products_data = self._load_products()
    
    def _load_seasonal_patterns(self):
        """Load seasonal patterns data"""
        patterns_path = Path(__file__).parent.parent / 'data' / 'seasonal_patterns.json'
        try:
            with open(patterns_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_seasonal_patterns()
    
    def _load_products(self):
        """Load products data"""
        products_path = Path(__file__).parent.parent / 'data' / 'products.json'
        try:
            with open(products_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _get_default_seasonal_patterns(self):
        """Return default seasonal patterns if file doesn't exist"""
        return {
            "Summer": {
                "Beverages": 1.5,
                "Fruits": 1.4,
                "Vegetables": 1.3,
                "Groceries": 1.0,
                "Personal Care": 1.2
            },
            "Winter": {
                "Beverages": 0.8,
                "Fruits": 0.9,
                "Vegetables": 1.2,
                "Groceries": 1.1,
                "Personal Care": 1.0
            },
            "Monsoon": {
                "Beverages": 1.2,
                "Fruits": 1.1,
                "Vegetables": 1.0,
                "Groceries": 1.3,
                "Personal Care": 1.4
            },
            "Regular": {
                "Beverages": 1.0,
                "Fruits": 1.0,
                "Vegetables": 1.0,
                "Groceries": 1.0,
                "Personal Care": 1.0
            }
        }
    
    def predict_stock_requirement(self, product_name, current_stock, season):
        """
        Predict stock requirement based on product, current stock, and season
        
        Args:
            product_name: Name of the product
            current_stock: Current stock level
            season: Season ('Summer', 'Winter', 'Monsoon', 'Regular')
        
        Returns:
            dict with prediction and recommendations
        """
        # Find product
        product = next((p for p in self.products_data if p['name'] == product_name), None)
        if not product:
            return self._get_default_prediction(product_name, current_stock, season)
        
        # Get category
        category = product.get('category', 'Groceries')
        
        # Get seasonal multiplier
        seasonal_multiplier = self.seasonal_patterns.get(season, {}).get(category, 1.0)
        
        # Calculate realistic base demand based on category
        base_demand = self._get_category_base_demand(category)
        predicted_demand = int(base_demand * seasonal_multiplier)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(current_stock, predicted_demand, season)
        
        return {
            'product': product_name,
            'category': category,
            'current_stock': current_stock,
            'season': season,
            'predicted_demand': predicted_demand,
            'seasonal_multiplier': seasonal_multiplier,
            'recommendation': recommendation,
            'price': product.get('current_price', 0),
            'unit': product.get('unit', 'pack')
        }
    
    def _get_category_base_demand(self, category):
        """Get realistic base demand for product category"""
        category_demands = {
            "Groceries": 150,
            "Dairy": 200,
            "Beverages": 180,
            "Fruits": 120,
            "Vegetables": 140,
            "Personal Care": 90,
            "Snacks": 160,
            "Frozen": 80,
            "Condiments": 70,
            "Miscellaneous": 100
        }
        return category_demands.get(category, 100)
    
    def _get_default_prediction(self, product_name, current_stock, season):
        """Get default prediction for unknown products"""
        seasonal_factors = {
            'Summer': 1.3,
            'Winter': 0.9,
            'Monsoon': 1.2,
            'Regular': 1.0
        }
        factor = seasonal_factors.get(season, 1.0)
        predicted_demand = int(100 * factor)
        
        recommendation = self._generate_recommendation(current_stock, predicted_demand, season)
        
        return {
            'product': product_name,
            'category': 'Miscellaneous',
            'current_stock': current_stock,
            'season': season,
            'predicted_demand': predicted_demand,
            'seasonal_multiplier': factor,
            'recommendation': recommendation,
            'price': 0,
            'unit': 'pack'
        }
    
    def _generate_recommendation(self, current_stock, predicted_demand, season):
        """Generate stock management recommendation"""
        safety_stock = int(predicted_demand * 0.2)  # 20% safety buffer
        reorder_point = predicted_demand
        optimal_stock = predicted_demand + safety_stock
        
        # Calculate required stock based on demand and availability
        required_stock = optimal_stock
        stock_gap = max(0, required_stock - current_stock)
        
        decision = "MAINTAIN"
        quantity_action = 0
        advice = ""
        
        if current_stock < reorder_point:
            decision = "ADD STOCK"
            quantity_action = optimal_stock - current_stock
            advice = f"Add {quantity_action} units"
        elif current_stock > optimal_stock * 1.5:
            decision = "REDUCE STOCK"
            quantity_action = current_stock - optimal_stock
            advice = f"Reduce by {quantity_action} units"
        else:
            quantity_action = current_stock  # Maintain current level
            advice = f"Maintain {current_stock} units"
        
        return {
            'decision': decision,
            'advice': advice,
            'quantity_action': quantity_action,
            'optimal_level': optimal_stock,
            'reorder_point': reorder_point,
            'safety_stock': safety_stock,
            'required_stock': required_stock,
            'stock_gap': stock_gap
        }
    
    def get_category_insights(self):
        """Get insights about all product categories"""
        categories = {}
        for product in self.products_data:
            category = product.get('category', 'Miscellaneous')
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'avg_price': 0,
                    'total_price': 0
                }
            categories[category]['count'] += 1
            categories[category]['total_price'] += product.get('current_price', 0)
        
        # Calculate averages
        for category in categories:
            if categories[category]['count'] > 0:
                categories[category]['avg_price'] = round(
                    categories[category]['total_price'] / categories[category]['count'], 2
                )
        
        return categories
