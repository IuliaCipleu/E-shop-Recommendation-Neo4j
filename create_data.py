from faker import Faker
import random, csv, datetime, os, time

faker = Faker()

def generate_dataset(scale='small'):
    scales = {
        'small':  {'users': 400, 'products': 100, 'categories': 10, 'orders': 440, 'wishlists': 50},
        'medium': {'users': 4000, 'products': 1000, 'categories': 15, 'orders': 4500, 'wishlists': 500},
        'large':  {'users': 40000, 'products': 10000, 'categories': 20, 'orders': 40000, 'wishlists': 10000}
    }

    cfg = scales[scale]
    outdir = f"neo4j_import/dataset_{scale}"
    os.makedirs(outdir, exist_ok=True)
    print(f"Generating {scale} dataset in '{outdir}'...")

    # Define realistic category profiles
    category_profiles = {
        "Electronics": {
            "description": "Devices such as phones, laptops, and home appliances.",
            "brands": ["Samsung", "Apple", "Sony", "LG", "Dell", "HP", "Asus"],
            "products": ["Smartphone", "Laptop", "Headphones", "Tablet", "Smartwatch", "Camera", "TV"],
            "price_range": (100, 2500)
        },
        "Books": {
            "description": "Printed and digital reading materials.",
            "brands": ["Penguin", "HarperCollins", "O'Reilly", "Vintage", "Macmillan"],
            "products": ["Novel", "Textbook", "Comics", "Biography", "Cookbook"],
            "price_range": (5, 100)
        },
        "Clothing": {
            "description": "Fashion and apparel for men and women.",
            "brands": ["Nike", "Adidas", "Zara", "H&M", "Uniqlo"],
            "products": ["T-shirt", "Jeans", "Jacket", "Dress", "Sneakers"],
            "price_range": (15, 300)
        },
        "Home": {
            "description": "Household essentials and furniture.",
            "brands": ["IKEA", "Philips", "Bosch", "Dyson", "Panasonic"],
            "products": ["Vacuum Cleaner", "Lamp", "Microwave", "Blender", "Air Purifier"],
            "price_range": (25, 700)
        },
        "Beauty": {
            "description": "Personal care and cosmetic products.",
            "brands": ["L'Oreal", "Nivea", "Dove", "Clinique", "Maybelline"],
            "products": ["Shampoo", "Perfume", "Lipstick", "Face Cream", "Body Lotion"],
            "price_range": (5, 150)
        }
    }

    # Fill remaining categories (if needed)
    category_names = list(category_profiles.keys())
    extra_needed = max(0, cfg['categories'] - len(category_names))
    extra_categories = [faker.word().capitalize() for _ in range(extra_needed)]

    all_categories = category_names + extra_categories[:extra_needed]

    # Categories CSV
    with open(f"{outdir}/categories.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(["category_id", "name", "description"])
        for i, cat in enumerate(all_categories):
            if cat in category_profiles:
                writer.writerow([i, cat, category_profiles[cat]["description"]])
            else:
                writer.writerow([i, cat, faker.sentence()])

    # Products CSV (category-aware)
    with open(f"{outdir}/products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(["product_id", "name", "price", "brand", "rating", "category_id"])
        for i in range(cfg['products']):
            cat_id = random.randint(0, len(all_categories) - 1)
            cat_name = all_categories[cat_id]
            if cat_name in category_profiles:
                profile = category_profiles[cat_name]
                product_name = random.choice(profile["products"]) + " " + faker.word().capitalize()
                brand = random.choice(profile["brands"])
                price = round(random.uniform(*profile["price_range"]), 2)
            else:
                product_name = faker.word().capitalize()
                brand = faker.company()
                price = round(random.uniform(5, 500), 2)
            writer.writerow([i, product_name, price, brand, round(random.uniform(1, 5), 1), cat_id])

    # Users
    with open(f"{outdir}/users.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(["user_id", "name", "email", "registration_date"])
        for i in range(cfg['users']):
            writer.writerow([i, faker.name(), faker.email(), faker.date_this_decade()])

    # Orders
    with open(f"{outdir}/orders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(["order_id", "user_id", "product_id", "timestamp", "quantity", "total_price"])
        for i in range(cfg['orders']):
            qty = random.randint(1, 3)
            price = round(random.uniform(5, 500), 2)
            writer.writerow([
                i, random.randint(0, cfg['users'] - 1), random.randint(0, cfg['products'] - 1),
                faker.date_time_this_year(), qty, qty * price
            ])

    # Wishlists
    with open(f"{outdir}/wishlists.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(["wishlist_id", "user_id", "product_id", "added_on"])
        for i in range(cfg['wishlists']):
            writer.writerow([
                i, random.randint(0, cfg['users'] - 1), random.randint(0, cfg['products'] - 1),
                faker.date_this_year()
            ])

#     print(f"✅ {scale.capitalize()} dataset generated successfully!")

#     print("\n📜 Use these Cypher commands in Neo4j Browser or Aura:")
#     print(f"""
# LOAD CSV WITH HEADERS FROM 'file:///dataset_{scale}/users.csv' AS row
# CREATE (:User {{
#     user_id: toInteger(row.user_id),
#     name: row.name,
#     email: row.email,
#     registration_date: date(row.registration_date)
# }});

# LOAD CSV WITH HEADERS FROM 'file:///dataset_{scale}/categories.csv' AS row
# CREATE (:Category {{
#     category_id: toInteger(row.category_id),
#     name: row.name,
#     description: row.description
# }});

# LOAD CSV WITH HEADERS FROM 'file:///dataset_{scale}/products.csv' AS row
# MATCH (c:Category {{category_id: toInteger(row.category_id)}})
# CREATE (p:Product {{
#     product_id: toInteger(row.product_id),
#     name: row.name,
#     price: toFloat(row.price),
#     brand: row.brand,
#     rating: toFloat(row.rating)
# }})
# CREATE (p)-[:BELONGS_TO]->(c);

# LOAD CSV WITH HEADERS FROM 'file:///dataset_{scale}/orders.csv' AS row
# MATCH (u:User {{user_id: toInteger(row.user_id)}}),
#       (p:Product {{product_id: toInteger(row.product_id)}})
# CREATE (u)-[:PLACED {{
#     order_id: toInteger(row.order_id),
#     timestamp: datetime(row.timestamp),
#     quantity: toInteger(row.quantity),
#     total_price: toFloat(row.total_price)
# }}]->(p);

# LOAD CSV WITH HEADERS FROM 'file:///dataset_{scale}/wishlists.csv' AS row
# MATCH (u:User {{user_id: toInteger(row.user_id)}}),
#       (p:Product {{product_id: toInteger(row.product_id)}})
# CREATE (u)-[:WISHLISTED {{added_on: date(row.added_on)}}]->(p);
# """)

def main():
    for scale in ['small', 'medium', 'large']:
        start = time.time()
        generate_dataset(scale)
        end = time.time()
        print(f"Elapsed for {scale}:", round(end - start, 2), "seconds")

if __name__ == "__main__":
    main()
