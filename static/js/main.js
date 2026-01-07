// D-Mart Smart Inventory Management System - Main JavaScript

let inventory = [];
let productsData = [];

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await loadProducts();
    await loadDashboardStats();
    setupEventListeners();
    // Load saved analyses from localStorage so stats persist across refresh
    try {
        const saved = localStorage.getItem('inventoryData');
        inventory = saved ? JSON.parse(saved) : [];
    } catch (e) {
        inventory = [];
    }
    updateTable();
    updateStats();
    updateQuickInsights();
});

// Load products
async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        productsData = await response.json();
    } catch (error) {
        console.error('Error loading products:', error);
    }
    renderProductOptions();
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/dashboard-stats');
        const stats = await response.json();
        
        document.getElementById('totalProducts').textContent = stats.total_products;
        // `avg_price` already contains currency formatting from backend
        document.getElementById('avgPrice').textContent = stats.avg_price;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    const form = document.getElementById('productForm');
    const productSelect = document.getElementById('productName');
    
    form.addEventListener('submit', handleFormSubmit);
    productSelect.addEventListener('change', updateQuickInsights);
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const productName = document.getElementById('productName').value;
    const season = document.getElementById('season').value;
    const stock = parseInt(document.getElementById('stock').value);
    
    if (!productName || !season || isNaN(stock)) {
        showNotification('Please fill all fields', 'error');
        return;
    }
    
    // Show loading
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span>⏳ Analyzing...</span>';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product: productName,
                season: season,
                stock: stock
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            showNotification(error.error || 'Failed to analyze product', 'error');
            return;
        }
        
        const result = await response.json();
        
        if (result && result.product) {
            inventory.push(result);
            // persist analyses locally so dashboard stays in sync after reload
            try { localStorage.setItem('inventoryData', JSON.stringify(inventory)); } catch(e) {}
            updateTable();
            updateStats();
            updateQuickInsights();
            showNotification('✓ Analysis completed successfully!', 'success');
            
            // Reset form
            document.getElementById('stock').value = '';
        } else {
            showNotification('Unexpected response format', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Network error. Please check your connection.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Update table
function updateTable() {
    const tableBody = document.getElementById('tableData');
    
    if (inventory.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    <div class="empty-icon">📊</div>
                    <p>No analysis yet. Start by adding a product above.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = inventory.map((item, index) => {
        const priority = item.recommendation?.decision?.includes('ADD') ? 'high' : 
                        item.recommendation?.decision?.includes('REDUCE') ? 'medium' : 'low';
        const priorityColor = priority === 'high' ? '#EF476F' : 
                             priority === 'medium' ? '#F77F00' : '#06D6A0';
        
        // Get quantity action
        const quantityAction = item.recommendation?.quantity_action || 0;
        let maintainText = '';
        
        if (item.recommendation?.decision?.includes('ADD')) {
            maintainText = `<strong style="color: #EF476F;">+${quantityAction}</strong> units`;
        } else if (item.recommendation?.decision?.includes('REDUCE')) {
            maintainText = `<strong style="color: #F77F00;">-${quantityAction}</strong> units`;
        } else {
            maintainText = `<strong style="color: #06D6A0;">${quantityAction}</strong> units`;
        }
        
        return `
            <tr style="animation: slideIn 0.5s ease ${index * 0.1}s both;">
                <td><strong>${item.product}</strong><br><small>${item.category}</small></td>
                <td><span style="padding: 0.25rem 0.75rem; background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border-radius: 6px;">${item.season}</span></td>
                <td><strong>${item.current_stock}</strong></td>
                <td><strong style="color: ${priorityColor};">${item.predicted_demand}</strong></td>
                <td><span style="font-weight: 600; color: ${priorityColor};">${item.recommendation.decision}</span></td>
                <td><strong>₹${item.price}</strong><br><small style="color: #666;">Unit: ${item.unit}</small></td>
                <td><span style="font-size: 0.85rem; padding: 0.4rem 0.7rem; background: ${priorityColor}15; color: ${priorityColor}; border-radius: 6px; display: inline-block; font-weight: 600;">${maintainText}</span></td>
            </tr>
        `;
    }).join('');
}

// Update statistics
function updateStats() {
    // Count low stock alerts (items that need ADD STOCK - current stock is below reorder point)
    const lowStockItems = inventory.filter(item => {
        return item.recommendation && 
               item.recommendation.decision && 
               item.recommendation.decision === 'ADD STOCK';
    }).length;
    
    // Count high demand items (non-regular seasons OR predicted demand exceeds current stock significantly)
    const highDemandItems = inventory.filter(item => {
        const isHighSeason = item.season !== 'Regular';
        const hasHighDemand = item.predicted_demand > item.current_stock;
        return isHighSeason || hasHighDemand;
    }).length;
    
    // Update dashboard stats
    document.getElementById('lowStock').textContent = lowStockItems;
    document.getElementById('highDemand').textContent = highDemandItems;
    
    console.log(`📊 Stats Updated - Low Stock Alerts: ${lowStockItems}, High Demand Items: ${highDemandItems}`);
}

// Update quick insights
function updateQuickInsights() {
    const productName = document.getElementById('productName').value;
    const insightsContainer = document.getElementById('quickInsights');
    
    if (!productName) {
        insightsContainer.innerHTML = '<p class="insight-item">Select a product to see insights</p>';
        return;
    }
    
    const product = productsData.find(p => p.name === productName);
    if (!product) return;
    
    // Base product info
    const insights = [
        `Category: ${product.category}`,
        `Current Price: ₹${product.current_price} per ${product.unit}`,
        `Historical Avg Price: ₹${product.historical_price_avg}`,
        `Price Trend: ${product.current_price > product.historical_price_avg ? 'Increasing' : 'Stable'}`
    ];

    // If we have a recent analysis for this product, show it
    const lastAnalysis = inventory.slice().reverse().find(i => i.product === productName);
    if (lastAnalysis) {
        insights.push(`Predicted Demand: ${lastAnalysis.predicted_demand} units`);
        insights.push(`Last Decision: ${lastAnalysis.recommendation?.decision || 'N/A'}`);
        const qty = lastAnalysis.recommendation?.quantity_action ?? 0;
        const qtyText = lastAnalysis.recommendation?.decision === 'ADD STOCK' ? `+${qty}` : lastAnalysis.recommendation?.decision === 'REDUCE STOCK' ? `-${qty}` : `${qty}`;
        insights.push(`Quantity Action: ${qtyText} units`);
    } else {
        insights.push('No recent analysis for this product');
    }
    
    insightsContainer.innerHTML = insights.map(insight =>
        `<p class="insight-item">${insight}</p>`
    ).join('');
}

// Render product options into the select element
function renderProductOptions() {
    const select = document.getElementById('productName');
    if (!select) return;

    // If server-side already rendered options, clear the placeholder options before adding
    // Keep the first placeholder option if present
    const placeholder = select.querySelector('option[value=""]');
    select.innerHTML = '';
    if (placeholder) select.appendChild(placeholder);

    productsData.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = `${p.name} - ${p.category || 'Miscellaneous'}`;
        select.appendChild(opt);
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#06D6A0' : '#EF476F'};
        color: white;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animation for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);
