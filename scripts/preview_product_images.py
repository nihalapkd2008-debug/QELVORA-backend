from pathlib import Path
from django.conf import settings
from products.models import Product
import json

products = Product.objects.select_related("category").order_by("id")

data = []

for product in products:
    data.append({
        "id": product.id,
        "name": product.name,
        "category": product.category.name,
        "price": str(product.price),
        "image": product.image or ""
    })

html = """
<!DOCTYPE html>
<html>
<head>
<title>QELVORA Product Preview</title>
<style>
body {
    font-family: Arial;
    background: #f5f3ef;
    padding: 25px;
}
h1 {
    text-align: center;
    letter-spacing: 5px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}
.card {
    background: white;
    padding: 12px;
}
img {
    width: 100%;
    height: 240px;
    object-fit: cover;
    background: #ddd;
}
</style>
</head>
<body>
<h1>QELVORA</h1>
<div class="grid">
"""

for item in data:
    html += f"""
    <div class="card">
        <img src="{item['image']}" alt="{item['name']}">
        <h3>{item['name']}</h3>
        <p>{item['category']}</p>
    </div>
    """

html += "</div></body></html>"

output = Path("qelvora_current_preview.html")
output.write_text(html, encoding="utf-8")

print("Preview created:", output.resolve())
print("Products:", len(data))