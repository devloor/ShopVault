"""
Management command to seed the database with products.
Creates 10+ categories with 10 products each using dummyjson.com API
supplemented with curated additional products.
"""
import urllib.request
import json
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.products.models import Product, Category


# Additional products to ensure at least 10 per category
EXTRA_PRODUCTS = {
    'Smartphones': [
        {'title': 'Galaxy S24 Ultra', 'description': 'Samsung flagship with AI features and S Pen', 'price': 1299.99, 'brand': 'Samsung', 'rating': 4.7, 'stock': 45, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/Samsung%20Galaxy%20S24/thumbnail.png'},
        {'title': 'iPhone 15 Pro Max', 'description': 'Apple flagship with titanium design and A17 Pro chip', 'price': 1199.99, 'brand': 'Apple', 'rating': 4.8, 'stock': 60, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/iPhone%2015%20Pro/thumbnail.png'},
        {'title': 'Pixel 8 Pro', 'description': 'Google phone with best-in-class camera and AI', 'price': 999.99, 'brand': 'Google', 'rating': 4.5, 'stock': 35, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/iPhone%20X/thumbnail.png'},
        {'title': 'OnePlus 12', 'description': 'Flagship killer with Snapdragon 8 Gen 3', 'price': 799.99, 'brand': 'OnePlus', 'rating': 4.4, 'stock': 40, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/iPhone%206/thumbnail.png'},
        {'title': 'Xiaomi 14 Ultra', 'description': 'Leica camera system with premium build', 'price': 899.99, 'brand': 'Xiaomi', 'rating': 4.3, 'stock': 30, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/Oppo%20A57/thumbnail.png'},
        {'title': 'Samsung Galaxy A54', 'description': 'Mid-range champion with great battery life', 'price': 449.99, 'brand': 'Samsung', 'rating': 4.2, 'stock': 80, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/Samsung%20Galaxy%20S24/thumbnail.png'},
        {'title': 'Nothing Phone 2', 'description': 'Unique transparent design with Glyph interface', 'price': 599.99, 'brand': 'Nothing', 'rating': 4.1, 'stock': 25, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/iPhone%20X/thumbnail.png'},
        {'title': 'Motorola Edge 40 Pro', 'description': 'Curved display with 165Hz refresh rate', 'price': 699.99, 'brand': 'Motorola', 'rating': 4.0, 'stock': 20, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/Oppo%20A57/thumbnail.png'},
        {'title': 'Sony Xperia 1 V', 'description': 'Pro-grade camera with 4K OLED display', 'price': 1399.99, 'brand': 'Sony', 'rating': 4.3, 'stock': 15, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/iPhone%2015%20Pro/thumbnail.png'},
        {'title': 'Realme GT 5 Pro', 'description': 'Performance flagship at an affordable price', 'price': 549.99, 'brand': 'Realme', 'rating': 4.0, 'stock': 50, 'thumbnail': 'https://cdn.dummyjson.com/products/images/smartphones/iPhone%206/thumbnail.png'},
    ],
    'Laptops': [
        {'title': 'MacBook Pro 16" M3 Max', 'description': 'Apple silicon powerhouse for professionals', 'price': 2499.99, 'brand': 'Apple', 'rating': 4.9, 'stock': 20, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Apple%20MacBook%20Pro%2014%20Inch%20Space%20Grey/thumbnail.png'},
        {'title': 'Dell XPS 15', 'description': 'InfinityEdge display with Intel Core Ultra', 'price': 1799.99, 'brand': 'Dell', 'rating': 4.5, 'stock': 30, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Lenovo%20Yoga%20920/thumbnail.png'},
        {'title': 'ThinkPad X1 Carbon Gen 11', 'description': 'Business ultrabook with legendary keyboard', 'price': 1649.99, 'brand': 'Lenovo', 'rating': 4.6, 'stock': 25, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Lenovo%20Yoga%20920/thumbnail.png'},
        {'title': 'ASUS ROG Strix G16', 'description': 'Gaming laptop with RTX 4070 and 240Hz display', 'price': 1599.99, 'brand': 'ASUS', 'rating': 4.4, 'stock': 35, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Asus%20Zenbook%20Pro%20Dual%20Screen/thumbnail.png'},
        {'title': 'HP Spectre x360', 'description': 'Premium 2-in-1 with OLED touchscreen', 'price': 1499.99, 'brand': 'HP', 'rating': 4.3, 'stock': 40, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/HP%20Pavilion%2015%20DK1056WM/thumbnail.png'},
        {'title': 'Razer Blade 15', 'description': 'Thin gaming laptop with NVIDIA GPU', 'price': 2299.99, 'brand': 'Razer', 'rating': 4.4, 'stock': 15, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Asus%20Zenbook%20Pro%20Dual%20Screen/thumbnail.png'},
        {'title': 'Acer Swift 5', 'description': 'Ultra-lightweight productivity laptop', 'price': 999.99, 'brand': 'Acer', 'rating': 4.1, 'stock': 55, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Lenovo%20Yoga%20920/thumbnail.png'},
        {'title': 'Microsoft Surface Laptop 5', 'description': '13.5" PixelSense touchscreen', 'price': 1299.99, 'brand': 'Microsoft', 'rating': 4.2, 'stock': 30, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/HP%20Pavilion%2015%20DK1056WM/thumbnail.png'},
        {'title': 'Samsung Galaxy Book3 Ultra', 'description': 'Super AMOLED display, Intel i9', 'price': 2199.99, 'brand': 'Samsung', 'rating': 4.3, 'stock': 18, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Apple%20MacBook%20Pro%2014%20Inch%20Space%20Grey/thumbnail.png'},
        {'title': 'Chromebook Plus', 'description': 'Google AI-powered ChromeOS laptop', 'price': 499.99, 'brand': 'Google', 'rating': 4.0, 'stock': 70, 'thumbnail': 'https://cdn.dummyjson.com/products/images/laptops/Lenovo%20Yoga%20920/thumbnail.png'},
    ],
    'Headphones': [
        {'title': 'Sony WH-1000XM5', 'description': 'Industry-leading noise cancelling headphones', 'price': 349.99, 'brand': 'Sony', 'rating': 4.8, 'stock': 50, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Apple AirPods Pro 2', 'description': 'Active noise cancellation with USB-C', 'price': 249.99, 'brand': 'Apple', 'rating': 4.7, 'stock': 80, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Bose QuietComfort Ultra', 'description': 'Premium comfort with spatial audio', 'price': 429.99, 'brand': 'Bose', 'rating': 4.6, 'stock': 40, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Sennheiser Momentum 4', 'description': 'Audiophile-grade wireless headphones', 'price': 349.99, 'brand': 'Sennheiser', 'rating': 4.5, 'stock': 30, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Samsung Galaxy Buds2 Pro', 'description': '360 Audio with Hi-Fi sound', 'price': 199.99, 'brand': 'Samsung', 'rating': 4.3, 'stock': 65, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'JBL Tour One M2', 'description': 'True adaptive noise cancelling', 'price': 299.99, 'brand': 'JBL', 'rating': 4.2, 'stock': 45, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Beats Studio Pro', 'description': 'Personalized spatial audio', 'price': 349.99, 'brand': 'Beats', 'rating': 4.1, 'stock': 35, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Audio-Technica ATH-M50x', 'description': 'Studio monitor headphones', 'price': 149.99, 'brand': 'Audio-Technica', 'rating': 4.6, 'stock': 60, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Jabra Elite 85t', 'description': 'Semi-open design with adjustable ANC', 'price': 229.99, 'brand': 'Jabra', 'rating': 4.2, 'stock': 50, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
        {'title': 'Skullcandy Crusher ANC 2', 'description': 'Adjustable sensory bass with ANC', 'price': 179.99, 'brand': 'Skullcandy', 'rating': 4.0, 'stock': 55, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mobile-accessories/Apple%20AirPods%20Max%20Silver/thumbnail.png'},
    ],
    'Books': [
        {'title': 'Atomic Habits', 'description': 'Tiny changes, remarkable results by James Clear', 'price': 16.99, 'brand': 'Penguin', 'rating': 4.8, 'stock': 200, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'The Psychology of Money', 'description': 'Timeless lessons on wealth by Morgan Housel', 'price': 14.99, 'brand': 'Harriman', 'rating': 4.7, 'stock': 180, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Sapiens', 'description': 'A brief history of humankind by Yuval Harari', 'price': 18.99, 'brand': 'Harper', 'rating': 4.6, 'stock': 150, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Deep Work', 'description': 'Rules for focused success by Cal Newport', 'price': 15.99, 'brand': 'Grand Central', 'rating': 4.5, 'stock': 120, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'The Lean Startup', 'description': 'How to build a successful business', 'price': 17.99, 'brand': 'Crown', 'rating': 4.4, 'stock': 100, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Thinking, Fast and Slow', 'description': 'Daniel Kahneman on decision making', 'price': 13.99, 'brand': 'FSG', 'rating': 4.5, 'stock': 110, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Zero to One', 'description': 'Startup notes by Peter Thiel', 'price': 14.99, 'brand': 'Crown', 'rating': 4.3, 'stock': 90, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'The Art of War', 'description': 'Ancient Chinese military strategy by Sun Tzu', 'price': 9.99, 'brand': 'Shambhala', 'rating': 4.6, 'stock': 250, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Rich Dad Poor Dad', 'description': 'Financial literacy by Robert Kiyosaki', 'price': 12.99, 'brand': 'Plata', 'rating': 4.4, 'stock': 160, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': '1984', 'description': 'Dystopian classic by George Orwell', 'price': 11.99, 'brand': 'Penguin', 'rating': 4.7, 'stock': 300, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
    ],
    'Clothing': [
        {'title': 'Classic Fit Cotton T-Shirt', 'description': '100% cotton, available in multiple colors', 'price': 24.99, 'brand': 'Amazon Essentials', 'rating': 4.3, 'stock': 500, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Slim Fit Jeans', 'description': 'Stretch denim for all-day comfort', 'price': 49.99, 'brand': 'Levis', 'rating': 4.4, 'stock': 300, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Hooded Sweatshirt', 'description': 'Fleece-lined hoodie with kangaroo pocket', 'price': 39.99, 'brand': 'Nike', 'rating': 4.5, 'stock': 250, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Down Puffer Jacket', 'description': 'Lightweight insulated jacket', 'price': 89.99, 'brand': 'Columbia', 'rating': 4.4, 'stock': 120, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Formal Dress Shirt', 'description': 'Wrinkle-free button-down', 'price': 34.99, 'brand': 'Van Heusen', 'rating': 4.2, 'stock': 180, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Athletic Running Shorts', 'description': 'Quick-dry fabric with liner', 'price': 29.99, 'brand': 'Under Armour', 'rating': 4.3, 'stock': 350, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Wool Blend Overcoat', 'description': 'Classic winter coat with notch lapel', 'price': 149.99, 'brand': 'Calvin Klein', 'rating': 4.5, 'stock': 60, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Cargo Pants', 'description': 'Utility pants with multiple pockets', 'price': 44.99, 'brand': 'Wrangler', 'rating': 4.1, 'stock': 200, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Graphic Print Sweater', 'description': 'Cozy knit with modern design', 'price': 54.99, 'brand': 'H&M', 'rating': 4.0, 'stock': 150, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
        {'title': 'Linen Summer Dress', 'description': 'Breathable midi dress for warm weather', 'price': 59.99, 'brand': 'Zara', 'rating': 4.4, 'stock': 100, 'thumbnail': 'https://cdn.dummyjson.com/products/images/tops/Blue%20Women%27s%20Handbag/thumbnail.png'},
    ],
    'Home & Kitchen': [
        {'title': 'Instant Pot Duo 7-in-1', 'description': 'Multi-use pressure cooker', 'price': 89.99, 'brand': 'Instant Pot', 'rating': 4.7, 'stock': 150, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'KitchenAid Stand Mixer', 'description': 'Professional 5-quart mixer', 'price': 349.99, 'brand': 'KitchenAid', 'rating': 4.8, 'stock': 40, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Dyson V15 Detect Vacuum', 'description': 'Cordless vacuum with laser detection', 'price': 649.99, 'brand': 'Dyson', 'rating': 4.6, 'stock': 30, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Ninja Professional Blender', 'description': '1000W motor with 72oz pitcher', 'price': 79.99, 'brand': 'Ninja', 'rating': 4.5, 'stock': 120, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Cast Iron Skillet 12"', 'description': 'Pre-seasoned cast iron pan', 'price': 44.99, 'brand': 'Lodge', 'rating': 4.7, 'stock': 200, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Memory Foam Pillow Set', 'description': 'Cooling gel memory foam, 2-pack', 'price': 39.99, 'brand': 'Beckham Hotel', 'rating': 4.4, 'stock': 300, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Robot Vacuum Cleaner', 'description': 'Smart mapping with app control', 'price': 299.99, 'brand': 'iRobot', 'rating': 4.3, 'stock': 80, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Air Fryer 5.8 QT', 'description': '8-in-1 digital air fryer', 'price': 69.99, 'brand': 'COSORI', 'rating': 4.6, 'stock': 180, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Egyptian Cotton Sheet Set', 'description': '1000 thread count luxury bedding', 'price': 89.99, 'brand': 'CGK Unlimited', 'rating': 4.5, 'stock': 100, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
        {'title': 'Stainless Steel Cookware Set', 'description': '10-piece tri-ply stainless set', 'price': 199.99, 'brand': 'All-Clad', 'rating': 4.7, 'stock': 50, 'thumbnail': 'https://cdn.dummyjson.com/products/images/kitchen-accessories/Bamboo%20Cutting%20Board/thumbnail.png'},
    ],
    'Sports & Outdoors': [
        {'title': 'Yoga Mat Premium', 'description': 'Non-slip exercise mat, 6mm thick', 'price': 29.99, 'brand': 'Gaiam', 'rating': 4.5, 'stock': 200, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'Resistance Bands Set', 'description': '5 levels of resistance for home workouts', 'price': 19.99, 'brand': 'Fit Simplify', 'rating': 4.4, 'stock': 350, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'Adjustable Dumbbell Set', 'description': '5-52.5 lbs adjustable weight', 'price': 349.99, 'brand': 'Bowflex', 'rating': 4.7, 'stock': 60, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'Running Shoes Ultraboost', 'description': 'Responsive Boost midsole', 'price': 189.99, 'brand': 'Adidas', 'rating': 4.6, 'stock': 150, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': '2-Person Camping Tent', 'description': 'Waterproof dome tent with rainfly', 'price': 79.99, 'brand': 'Coleman', 'rating': 4.3, 'stock': 90, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'Insulated Water Bottle 32oz', 'description': 'Vacuum insulated stainless steel', 'price': 34.99, 'brand': 'Hydro Flask', 'rating': 4.7, 'stock': 400, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'GPS Sports Watch', 'description': 'Heart rate monitor with GPS tracking', 'price': 249.99, 'brand': 'Garmin', 'rating': 4.5, 'stock': 80, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'Foam Roller', 'description': 'High-density muscle recovery roller', 'price': 24.99, 'brand': 'TriggerPoint', 'rating': 4.4, 'stock': 250, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'Jump Rope Speed', 'description': 'Adjustable weighted speed rope', 'price': 14.99, 'brand': 'Crossrope', 'rating': 4.3, 'stock': 300, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
        {'title': 'Hiking Backpack 50L', 'description': 'Lightweight trekking pack with rain cover', 'price': 69.99, 'brand': 'Osprey', 'rating': 4.6, 'stock': 70, 'thumbnail': 'https://cdn.dummyjson.com/products/images/sports-accessories/Cricket%20Bat/thumbnail.png'},
    ],
    'Toys & Games': [
        {'title': 'LEGO Star Wars Millennium Falcon', 'description': '1353-piece building set', 'price': 159.99, 'brand': 'LEGO', 'rating': 4.8, 'stock': 60, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Nintendo Switch OLED', 'description': '7-inch OLED screen gaming console', 'price': 349.99, 'brand': 'Nintendo', 'rating': 4.7, 'stock': 80, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Monopoly Classic', 'description': 'The classic family board game', 'price': 19.99, 'brand': 'Hasbro', 'rating': 4.4, 'stock': 200, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Rubiks Cube 3x3', 'description': 'Classic speed cube puzzle', 'price': 9.99, 'brand': 'Rubiks', 'rating': 4.5, 'stock': 500, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Play-Doh 36-Pack', 'description': 'Non-toxic modeling compound', 'price': 24.99, 'brand': 'Play-Doh', 'rating': 4.6, 'stock': 300, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Remote Control Car', 'description': 'High-speed RC car with rechargeable battery', 'price': 44.99, 'brand': 'DEERC', 'rating': 4.2, 'stock': 120, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Wooden Puzzle Set', 'description': 'Educational puzzle for kids 3+', 'price': 14.99, 'brand': 'Melissa & Doug', 'rating': 4.5, 'stock': 250, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Nerf Elite 2.0', 'description': 'Motorized dart blaster', 'price': 34.99, 'brand': 'Nerf', 'rating': 4.3, 'stock': 150, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Hot Wheels Track Builder', 'description': 'Customizable car track set', 'price': 29.99, 'brand': 'Hot Wheels', 'rating': 4.4, 'stock': 180, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
        {'title': 'Chess Set Wood', 'description': 'Handcrafted wooden chess set', 'price': 39.99, 'brand': 'Yellow Mountain', 'rating': 4.6, 'stock': 90, 'thumbnail': 'https://cdn.dummyjson.com/products/images/groceries/Apple/thumbnail.png'},
    ],
    'Health & Personal Care': [
        {'title': 'Electric Toothbrush Pro', 'description': 'Sonic cleaning with 5 modes', 'price': 69.99, 'brand': 'Oral-B', 'rating': 4.6, 'stock': 150, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Vitamin D3 5000 IU', 'description': '360 softgels daily supplement', 'price': 14.99, 'brand': 'NatureWise', 'rating': 4.7, 'stock': 400, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Hair Dryer Ionic', 'description': 'Fast drying with diffuser attachment', 'price': 49.99, 'brand': 'Revlon', 'rating': 4.3, 'stock': 120, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'First Aid Kit 300-Piece', 'description': 'Comprehensive emergency supplies', 'price': 29.99, 'brand': 'Be Smart Get Prepared', 'rating': 4.5, 'stock': 200, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Whey Protein Powder 5lb', 'description': 'Gold standard protein shake mix', 'price': 59.99, 'brand': 'Optimum Nutrition', 'rating': 4.6, 'stock': 250, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Digital Thermometer', 'description': 'Fast-read infrared thermometer', 'price': 19.99, 'brand': 'Braun', 'rating': 4.4, 'stock': 350, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Sunscreen SPF 50', 'description': 'Broad spectrum face sunscreen', 'price': 15.99, 'brand': 'Neutrogena', 'rating': 4.3, 'stock': 300, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Massage Gun', 'description': 'Deep tissue percussion massager', 'price': 99.99, 'brand': 'Theragun', 'rating': 4.5, 'stock': 80, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Blood Pressure Monitor', 'description': 'Automatic upper arm monitor', 'price': 39.99, 'brand': 'Omron', 'rating': 4.6, 'stock': 100, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
        {'title': 'Melatonin Sleep Gummies', 'description': '10mg natural sleep aid, 60 count', 'price': 12.99, 'brand': 'Olly', 'rating': 4.2, 'stock': 500, 'thumbnail': 'https://cdn.dummyjson.com/products/images/skin-care/Skin%20Beauty%20Serum/thumbnail.png'},
    ],
    'Watches': [
        {'title': 'Apple Watch Series 9', 'description': 'Advanced health monitoring smartwatch', 'price': 399.99, 'brand': 'Apple', 'rating': 4.7, 'stock': 70, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Samsung Galaxy Watch 6', 'description': 'Wear OS smartwatch with BIA sensor', 'price': 299.99, 'brand': 'Samsung', 'rating': 4.4, 'stock': 90, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Casio G-Shock GA2100', 'description': 'Carbon core guard structure', 'price': 99.99, 'brand': 'Casio', 'rating': 4.6, 'stock': 150, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Timex Weekender', 'description': 'Classic analog watch with NATO strap', 'price': 39.99, 'brand': 'Timex', 'rating': 4.3, 'stock': 200, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Fossil Gen 6 Hybrid', 'description': 'Smart features in classic design', 'price': 229.99, 'brand': 'Fossil', 'rating': 4.2, 'stock': 80, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Seiko Presage Automatic', 'description': 'Japanese mechanical dress watch', 'price': 425.99, 'brand': 'Seiko', 'rating': 4.7, 'stock': 30, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Fitbit Versa 4', 'description': 'Fitness and wellness smartwatch', 'price': 199.99, 'brand': 'Fitbit', 'rating': 4.3, 'stock': 110, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Citizen Eco-Drive', 'description': 'Solar-powered stainless steel watch', 'price': 275.00, 'brand': 'Citizen', 'rating': 4.5, 'stock': 50, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Daniel Wellington Classic', 'description': 'Minimalist leather strap watch', 'price': 149.99, 'brand': 'Daniel Wellington', 'rating': 4.1, 'stock': 120, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
        {'title': 'Garmin Venu 3', 'description': 'GPS smartwatch with AMOLED display', 'price': 449.99, 'brand': 'Garmin', 'rating': 4.6, 'stock': 45, 'thumbnail': 'https://cdn.dummyjson.com/products/images/mens-watches/Brown%20Leather%20Belt%20Watch/thumbnail.png'},
    ],
}


class Command(BaseCommand):
    help = 'Seeds the database with products — 10+ categories with 10 products each'

    def handle(self, *args, **options):
        # First fetch from dummyjson.com
        self.stdout.write('Fetching products from dummyjson.com...')
        url = 'https://dummyjson.com/products?limit=100&skip=0'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to fetch data: {e}'))
            data = {'products': []}

        api_products = data.get('products', [])
        created_count = 0

        # Process API products
        for item in api_products:
            category_name = item.get('category', 'General')
            category_name = category_name.replace('-', ' ').title().strip()
            category, _ = Category.objects.get_or_create(name=category_name)

            images = item.get('images', [])
            image_url = images[0] if images else ''
            thumbnail = item.get('thumbnail', image_url)

            title = item.get('title', '').strip()[:200]
            if not title:
                continue

            product, created = Product.objects.get_or_create(
                title=title,
                defaults={
                    'description': item.get('description', '')[:2000],
                    'price': max(float(item.get('price', 0)), 0.01),
                    'category': category,
                    'image_url': image_url,
                    'thumbnail': thumbnail,
                    'rating': min(max(float(item.get('rating', 0)), 0), 5),
                    'stock': max(int(item.get('stock', 0)), 0),
                    'brand': item.get('brand', '')[:100],
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} products from API')

        # Now add extra curated products
        extra_count = 0
        for cat_name, products in EXTRA_PRODUCTS.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            for item in products:
                product, created = Product.objects.get_or_create(
                    title=item['title'],
                    defaults={
                        'description': item['description'],
                        'price': Decimal(str(item['price'])),
                        'category': category,
                        'image_url': item.get('thumbnail', ''),
                        'thumbnail': item.get('thumbnail', ''),
                        'rating': Decimal(str(item['rating'])),
                        'stock': item['stock'],
                        'brand': item['brand'],
                    }
                )
                if created:
                    extra_count += 1

        self.stdout.write(f'  Created {extra_count} extra curated products')

        # Summary
        total = Product.objects.count()
        cats = Category.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Total: {total} products across {cats} categories.'
        ))
        for cat in Category.objects.all():
            count = cat.products.count()
            self.stdout.write(f'  {cat.name}: {count} products')
