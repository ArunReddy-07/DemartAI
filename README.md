# D-Mart Smart Inventory Management System

An intelligent inventory management system for retail stores with AI-powered recommendations, seasonal analysis, and smart chatbot assistant.

## Features

✨ **Smart Inventory Management**
- Real-time inventory analysis
- Seasonal demand forecasting
- Stock optimization recommendations
- Automated reorder point calculations

📊 **Advanced Analytics**
- Category-wise distribution
- Price trend analysis
- Seasonal pattern insights
- Demand forecasting

🤖 **AI Chatbot Assistant**
- Google Gemini-powered responses
- Inventory management advice
- Pricing strategy recommendations
- Quick suggestion buttons

## Tech Stack

- **Backend**: Flask 3.0.0
- **AI Integration**: Google Generative AI (Gemini)
- **Data Processing**: NumPy, Pandas
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: JSON-based data storage

## Project Structure

```
dmartai/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── README.md              # This file
├── data/
│   ├── products.json      # Product catalog
│   └── seasonal_patterns.json  # Seasonal demand patterns
├── models/
│   └── predictor.py       # Inventory prediction model
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   └── js/
│       ├── main.js        # Dashboard functionality
│       └── chatbot.js     # Chatbot integration
└── templates/
    ├── base.html          # Base template
    ├── index.html         # Dashboard page
    └── analytics.html     # Analytics page
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Google API Key (for Gemini integration)

### Steps

1. **Clone/Navigate to the project directory**
   ```bash
   cd dmartai
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Open `.env` file
   - Add your Google API Key:
     ```
     GOOGLE_API_KEY=your-api-key-here
     ```
   - Get your free API key from: https://makersuite.google.com/app/apikey

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   - Navigate to `http://localhost:5000`

## Usage

### Dashboard
- View total products and statistics
- Select a product from the dropdown
- Choose a season (Summer, Winter, Monsoon, Regular, or Festival)
- Enter current stock level
- Get AI-powered recommendations

### Analytics Page
- View comprehensive analytics charts
- Analyze pricing trends
- Understand seasonal demand patterns
- See category distribution

### AI Chatbot
- Ask questions about inventory management
- Get pricing strategy recommendations
- Learn about seasonal trends
- Use quick suggestion buttons for common questions

## API Endpoints

### GET `/api/products`
Get all products in the catalog.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Basmati Rice (5kg)",
    "category": "Groceries",
    "current_price": 425,
    "historical_price_avg": 380,
    "unit": "pack"
  }
]
```

### GET `/api/dashboard-stats`
Get dashboard statistics.

**Response:**
```json
{
  "total_products": 200,
  "categories": ["Groceries", "Beverages", ...],
  "avg_price": "₹245.50",
  "category_distribution": {...}
}
```

### POST `/api/analyze`
Analyze inventory for a product.

**Request:**
```json
{
  "product": "Basmati Rice (5kg)",
  "season": "Summer",
  "stock": 50
}
```

**Response:**
```json
{
  "product": "Basmati Rice (5kg)",
  "category": "Groceries",
  "current_stock": 50,
  "season": "Summer",
  "predicted_demand": 100,
  "recommendation": {
    "decision": "ADD STOCK",
    "advice": "Add 40 units...",
    "optimal_level": 120,
    "reorder_point": 100,
    "safety_stock": 20
  }
}
```

### POST `/api/chat`
Send a message to the AI chatbot.

**Request:**
```json
{
  "message": "What are seasonal trends for dairy products?"
}
```

**Response:**
```json
{
  "response": "Dairy products have...",
  "status": "success"
}
```

## Seasonal Patterns

The system recognizes the following seasons:
- **Summer**: High demand for beverages and fruits
- **Winter**: Increased dairy and bakery product demand
- **Monsoon**: Higher demand for groceries and personal care
- **Regular**: Standard demand levels
- **Diwali/Holi/NewYear**: Festival seasons with boosted demand

## Configuration

Edit `config.py` to customize:
- Debug mode
- Secret key
- API configurations
- Environment settings

## Troubleshooting

### Chatbot not responding
- Check if `GOOGLE_API_KEY` is set in `.env`
- Verify API key is valid at https://makersuite.google.com
- Check internet connection
- System will fall back to default responses if API is unavailable

### Products not loading
- Ensure `data/products.json` exists and is valid JSON
- Check file permissions
- Verify JSON syntax

### Port already in use
- Change PORT in `.env` to an available port
- Or stop the application using the port

## Future Enhancements

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] User authentication and roles
- [ ] Real-time inventory tracking
- [ ] Mobile app
- [ ] Advanced ML models
- [ ] Integration with barcode scanners
- [ ] Email notifications
- [ ] Export reports to PDF/Excel

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions, please refer to the documentation or contact support.

---

**Made with ❤️ for smart retail management**
