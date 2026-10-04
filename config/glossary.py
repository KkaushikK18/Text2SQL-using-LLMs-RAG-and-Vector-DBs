GLOSSARY = {
    "revenue": "Revenue is ALWAYS calculated by summing the `subtotal` (or `quantity * unit_price`) from the `order_items` table. NEVER sum the `price` in `products` directly.",
    "sales": "Sales refers to the sum of `subtotal` from the `order_items` table.",
    "vip customer": "A VIP customer is a customer whose total sum of `total_amount` in `orders` is strictly greater than 1000.",
    "churned": "A customer is considered churned if they haven't placed an order in the last 6 months.",
    "active order": "An active order is any order with status 'processing' or 'shipped'."
}

def get_business_rules(question: str) -> str:
    """
    Acts as a Semantic Layer / Business Glossary.
    Scans the question for business terms and returns the strict SQL logic definitions.
    """
    rules = []
    q_lower = question.lower()
    for key, rule in GLOSSARY.items():
        if key in q_lower:
            rules.append(f"- {rule}")
            
    return "\n".join(rules) if rules else "No specific business rules apply."
