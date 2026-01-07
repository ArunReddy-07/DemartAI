from database import get_recent_analyses

if __name__ == '__main__':
    analyses = get_recent_analyses(1000)
    offers = []
    seen = set()
    for a in analyses:
        product = a.get('product_name') or a.get('product')
        if not product or product in seen:
            continue
        seen.add(product)
        current = int(a.get('current_stock') or 0)
        predicted = int(a.get('predicted_demand') or 0)
        item_offers = []
        if predicted > 0 and current > predicted:
            item_offers.append({
                'type': 'DISCOUNT',
                'discount_percent': 20,
                'message': f'Apply 20% discount on {product} to boost sales.'
            })
        if predicted > 0 and current >= int(predicted * 1.5):
            item_offers.append({
                'type': 'BOGO',
                'message': f'Offer Buy-One-Get-One for {product} to clear excess stock.'
            })
        if item_offers:
            offers.append({
                'product_name': product,
                'category': a.get('category'),
                'current_stock': current,
                'predicted_demand': predicted,
                'offers': item_offers
            })

    if not offers:
        print('No offer-eligible products found in recent analyses.')
    else:
        print(f"Found {len(offers)} offer-eligible products:\n")
        for o in offers:
            print(f"- {o['product_name']} (stock={o['current_stock']}, predicted={o['predicted_demand']})")
            for off in o['offers']:
                if off['type'] == 'DISCOUNT':
                    print(f"   • Discount: {off['discount_percent']}% - {off['message']}")
                else:
                    print(f"   • {off['type']}: {off['message']}")
