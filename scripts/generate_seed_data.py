"""
Generate synthetic wardrobe data for development.

random.seed(42) ensures full reproducibility.

Outputs:
  data/seed/wardrobe_items.json   - 60 wardrobe items
  data/eval/ragas_queries.json    - 50 RAGAS evaluation queries
"""

import json
import os
import random
from datetime import datetime, timedelta

random.seed(42)

BASE_DATE = datetime(2026, 4, 11)
OUT_ITEMS = os.path.join("data", "seed", "wardrobe_items.json")
OUT_EVAL  = os.path.join("data", "eval",  "ragas_queries.json")

# ---------------------------------------------------------------------------
# 60-item wardrobe definition
# Dates are assigned after definition using seeded random.
# ---------------------------------------------------------------------------
ITEMS_RAW = [
    # ── TOPS  item_001 – item_015 ───────────────────────────────────────────
    {
        "id": "item_001", "name": "White Oxford Shirt",
        "category": "tops", "subcategory": "shirt",
        "color": "white", "color_family": "neutral", "material": "cotton",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["classic", "minimal", "clean"],
        "notes": "slim fit, works tucked or untucked",
    },
    {
        "id": "item_002", "name": "Light Blue Chambray Shirt",
        "category": "tops", "subcategory": "shirt",
        "color": "light blue", "color_family": "cool", "material": "cotton",
        "formality": 2,
        "occasions": ["casual", "weekend", "smart-casual"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["relaxed", "casual", "american"],
        "notes": "slightly oversized, roll the sleeves",
    },
    {
        "id": "item_003", "name": "Charcoal Merino Sweater",
        "category": "tops", "subcategory": "sweater",
        "color": "charcoal", "color_family": "neutral", "material": "merino wool",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["minimal", "classic", "cosy"],
        "notes": "crew neck, fine gauge — layer under blazer",
    },
    {
        "id": "item_004", "name": "Black Turtleneck",
        "category": "tops", "subcategory": "turtleneck",
        "color": "black", "color_family": "neutral", "material": "wool-blend",
        "formality": 3,
        "occasions": ["dinner", "work", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["minimal", "classic", "sleek"],
        "notes": "fitted cut, pairs with tailored trousers",
    },
    {
        "id": "item_005", "name": "Striped Breton Top",
        "category": "tops", "subcategory": "t-shirt",
        "color": "navy/white", "color_family": "cool", "material": "cotton",
        "formality": 1,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["nautical", "casual", "french"],
        "notes": "classic navy stripes",
    },
    {
        "id": "item_006", "name": "White Linen Shirt",
        "category": "tops", "subcategory": "shirt",
        "color": "white", "color_family": "neutral", "material": "linen",
        "formality": 2,
        "occasions": ["casual", "dinner", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["relaxed", "minimal", "warm-weather"],
        "notes": "breathable, wrinkles are expected and fine",
    },
    {
        "id": "item_007", "name": "Grey Crewneck Sweatshirt",
        "category": "tops", "subcategory": "sweatshirt",
        "color": "grey", "color_family": "neutral", "material": "cotton-blend",
        "formality": 1,
        "occasions": ["casual", "gym", "weekend"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["casual", "streetwear", "basic"],
        "notes": "midweight, works for errands and gym warm-up",
    },
    {
        "id": "item_008", "name": "Ivory Silk Blouse",
        "category": "tops", "subcategory": "blouse",
        "color": "ivory", "color_family": "neutral", "material": "silk",
        "formality": 4,
        "occasions": ["dinner", "wedding-guest", "work"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["elegant", "classic", "feminine"],
        "notes": "dry clean only, handle with care",
    },
    {
        "id": "item_009", "name": "Olive Henley",
        "category": "tops", "subcategory": "henley",
        "color": "olive", "color_family": "warm", "material": "cotton",
        "formality": 2,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["casual", "relaxed", "earthy"],
        "notes": "3-button placket, relaxed fit",
    },
    {
        "id": "item_010", "name": "Camel Cashmere Sweater",
        "category": "tops", "subcategory": "sweater",
        "color": "camel", "color_family": "warm", "material": "cashmere",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "luxe", "cosy"],
        "notes": "hand wash cold, dry flat",
    },
    {
        "id": "item_011", "name": "Black Fitted T-Shirt",
        "category": "tops", "subcategory": "t-shirt",
        "color": "black", "color_family": "neutral", "material": "cotton",
        "formality": 1,
        "occasions": ["casual", "gym", "weekend"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "basic", "versatile"],
        "notes": "slightly fitted, goes under everything",
    },
    {
        "id": "item_012", "name": "Burgundy Knit Polo",
        "category": "tops", "subcategory": "polo",
        "color": "burgundy", "color_family": "warm", "material": "merino wool",
        "formality": 2,
        "occasions": ["casual", "smart-casual", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["preppy", "classic", "smart"],
        "notes": "can dress up with chinos",
    },
    {
        "id": "item_013", "name": "Denim Shirt",
        "category": "tops", "subcategory": "shirt",
        "color": "mid blue", "color_family": "cool", "material": "denim",
        "formality": 2,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["casual", "american", "relaxed"],
        "notes": "wear open over a tee or fully buttoned",
    },
    {
        "id": "item_014", "name": "Cream Ribbed Tank",
        "category": "tops", "subcategory": "tank",
        "color": "cream", "color_family": "neutral", "material": "cotton",
        "formality": 1,
        "occasions": ["casual", "gym", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["minimal", "basic", "summer"],
        "notes": "good base layer or standalone in warm weather",
    },
    {
        "id": "item_015", "name": "Navy Ribbed Turtleneck",
        "category": "tops", "subcategory": "turtleneck",
        "color": "navy", "color_family": "cool", "material": "cotton-blend",
        "formality": 3,
        "occasions": ["work", "smart-casual", "dinner"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "minimal", "preppy"],
        "notes": "ribbed texture, not as warm as wool — good for layering",
    },

    # ── BOTTOMS  item_016 – item_027 ────────────────────────────────────────
    {
        "id": "item_016", "name": "Dark Indigo Slim Jeans",
        "category": "bottoms", "subcategory": "jeans",
        "color": "dark indigo", "color_family": "cool", "material": "denim",
        "formality": 2,
        "occasions": ["casual", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "slim", "versatile"],
        "notes": "can pass as smart-casual when paired with a blazer",
    },
    {
        "id": "item_017", "name": "Black Skinny Jeans",
        "category": "bottoms", "subcategory": "jeans",
        "color": "black", "color_family": "neutral", "material": "denim",
        "formality": 2,
        "occasions": ["casual", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "minimal", "slim"],
        "notes": "slim through thigh and calf",
    },
    {
        "id": "item_018", "name": "Charcoal Wool Trousers",
        "category": "bottoms", "subcategory": "trousers",
        "color": "charcoal", "color_family": "neutral", "material": "wool",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "tailored", "formal"],
        "notes": "dry clean, crease front",
    },
    {
        "id": "item_019", "name": "Navy Chinos",
        "category": "bottoms", "subcategory": "chinos",
        "color": "navy", "color_family": "cool", "material": "cotton",
        "formality": 3,
        "occasions": ["work", "smart-casual", "dinner"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["preppy", "classic", "smart"],
        "notes": "slim cut, versatile — dress up or down",
    },
    {
        "id": "item_020", "name": "Beige Slim Chinos",
        "category": "bottoms", "subcategory": "chinos",
        "color": "beige", "color_family": "neutral", "material": "cotton",
        "formality": 3,
        "occasions": ["work", "smart-casual", "dinner"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["minimal", "classic", "clean"],
        "notes": "stone/khaki tone — good neutral base",
    },
    {
        "id": "item_021", "name": "Black Tailored Trousers",
        "category": "bottoms", "subcategory": "trousers",
        "color": "black", "color_family": "neutral", "material": "polyester-blend",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "tailored", "formal"],
        "notes": "high-waist, wide leg — very flattering",
    },
    {
        "id": "item_022", "name": "Camel Wide-Leg Trousers",
        "category": "bottoms", "subcategory": "trousers",
        "color": "camel", "color_family": "warm", "material": "wool-blend",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["editorial", "relaxed", "warm"],
        "notes": "high waist, pairs well with tucked-in tops",
    },
    {
        "id": "item_023", "name": "Dark Green Slim Jeans",
        "category": "bottoms", "subcategory": "jeans",
        "color": "dark green", "color_family": "warm", "material": "denim",
        "formality": 2,
        "occasions": ["casual", "weekend", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["casual", "colourful", "earthy"],
        "notes": "statement colour — keep rest of outfit neutral",
    },
    {
        "id": "item_024", "name": "White Linen Trousers",
        "category": "bottoms", "subcategory": "trousers",
        "color": "white", "color_family": "neutral", "material": "linen",
        "formality": 2,
        "occasions": ["casual", "beach", "dinner"],
        "seasons": ["spring", "summer"],
        "style_tags": ["minimal", "relaxed", "summer"],
        "notes": "slightly wide leg, very breathable",
    },
    {
        "id": "item_025", "name": "Black Athletic Shorts",
        "category": "bottoms", "subcategory": "shorts",
        "color": "black", "color_family": "neutral", "material": "polyester",
        "formality": 1,
        "occasions": ["gym"],
        "seasons": ["spring", "summer"],
        "style_tags": ["athletic", "functional", "basic"],
        "notes": "5-inch inseam, moisture-wicking",
    },
    {
        "id": "item_026", "name": "Grey Joggers",
        "category": "bottoms", "subcategory": "joggers",
        "color": "grey", "color_family": "neutral", "material": "cotton",
        "formality": 1,
        "occasions": ["gym", "casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["casual", "athletic", "comfort"],
        "notes": "tapered fit, good for home and gym",
    },
    {
        "id": "item_027", "name": "Rust Midi Wrap Skirt",
        "category": "bottoms", "subcategory": "skirt",
        "color": "rust", "color_family": "warm", "material": "viscose",
        "formality": 3,
        "occasions": ["dinner", "work", "smart-casual"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["feminine", "bohemian", "warm"],
        "notes": "bias cut, very flattering — tuck in a top",
    },

    # ── OUTERWEAR  item_028 – item_035 ──────────────────────────────────────
    {
        "id": "item_028", "name": "Navy Slim Blazer",
        "category": "outerwear", "subcategory": "blazer",
        "color": "navy", "color_family": "cool", "material": "wool-blend",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview", "wedding-guest", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "tailored", "versatile"],
        "notes": "single-breasted, two-button — workhorse blazer",
    },
    {
        "id": "item_029", "name": "Camel Trench Coat",
        "category": "outerwear", "subcategory": "trench coat",
        "color": "camel", "color_family": "warm", "material": "cotton",
        "formality": 4,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter", "spring"],
        "style_tags": ["classic", "elegant", "timeless"],
        "notes": "belted, water-resistant shell",
    },
    {
        "id": "item_030", "name": "Black Leather Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 2,
        "occasions": ["casual", "dinner", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["edgy", "cool", "rock"],
        "notes": "slim fit moto-style",
    },
    {
        "id": "item_031", "name": "Charcoal Overcoat",
        "category": "outerwear", "subcategory": "coat",
        "color": "charcoal", "color_family": "neutral", "material": "wool",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "minimal", "formal"],
        "notes": "double-breasted, knee length",
    },
    {
        "id": "item_032", "name": "Olive Utility Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "olive", "color_family": "warm", "material": "cotton",
        "formality": 2,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["casual", "utilitarian", "earthy"],
        "notes": "multiple pockets, works with jeans or chinos",
    },
    {
        "id": "item_033", "name": "Grey Puffer Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "light grey", "color_family": "neutral", "material": "nylon",
        "formality": 1,
        "occasions": ["casual", "gym", "weekend"],
        "seasons": ["winter"],
        "style_tags": ["casual", "functional", "warm"],
        "notes": "packable, 650-fill down",
    },
    {
        "id": "item_034", "name": "Burgundy Blazer",
        "category": "outerwear", "subcategory": "blazer",
        "color": "burgundy", "color_family": "warm", "material": "wool-blend",
        "formality": 4,
        "occasions": ["dinner", "smart-casual", "wedding-guest"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "bold", "statement"],
        "notes": "unlined, more relaxed feel than the navy",
    },
    {
        "id": "item_035", "name": "Navy Denim Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "navy", "color_family": "cool", "material": "denim",
        "formality": 2,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["casual", "american", "classic"],
        "notes": "classic fit, slightly oversized",
    },

    # ── SHOES  item_036 – item_045 ──────────────────────────────────────────
    {
        "id": "item_036", "name": "White Leather Sneakers",
        "category": "shoes", "subcategory": "sneakers",
        "color": "white", "color_family": "neutral", "material": "leather",
        "formality": 1,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["minimal", "clean", "versatile"],
        "notes": "Stan Smith style — keep very clean",
    },
    {
        "id": "item_037", "name": "Black Oxford Shoes",
        "category": "shoes", "subcategory": "oxfords",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 5,
        "occasions": ["job-interview", "dinner", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "formal", "dress"],
        "notes": "cap toe, resoled — keep polished",
    },
    {
        "id": "item_038", "name": "Tan Derby Shoes",
        "category": "shoes", "subcategory": "derby",
        "color": "tan", "color_family": "warm", "material": "leather",
        "formality": 3,
        "occasions": ["work", "smart-casual", "dinner"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "warm", "smart"],
        "notes": "open lacing — slightly more casual than oxford",
    },
    {
        "id": "item_039", "name": "White Canvas Sneakers",
        "category": "shoes", "subcategory": "sneakers",
        "color": "white", "color_family": "neutral", "material": "canvas",
        "formality": 1,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["casual", "basic", "summer"],
        "notes": "machine washable",
    },
    {
        "id": "item_040", "name": "Black Chelsea Boots",
        "category": "shoes", "subcategory": "chelsea boots",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "versatile", "smart"],
        "notes": "elastic gusset — easy on/off, pairs with almost everything",
    },
    {
        "id": "item_041", "name": "Tan Suede Loafers",
        "category": "shoes", "subcategory": "loafers",
        "color": "tan", "color_family": "warm", "material": "suede",
        "formality": 3,
        "occasions": ["work", "smart-casual", "dinner"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["preppy", "relaxed", "smart"],
        "notes": "avoid in wet weather — suede scuffs easily",
    },
    {
        "id": "item_042", "name": "Black Running Sneakers",
        "category": "shoes", "subcategory": "sneakers",
        "color": "black", "color_family": "neutral", "material": "synthetic",
        "formality": 1,
        "occasions": ["gym"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["athletic", "functional"],
        "notes": "dedicated to running only — keep clean",
    },
    {
        "id": "item_043", "name": "Brown Leather Boots",
        "category": "shoes", "subcategory": "boots",
        "color": "brown", "color_family": "warm", "material": "leather",
        "formality": 3,
        "occasions": ["casual", "dinner", "weekend"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "rugged", "warm"],
        "notes": "ankle height, chunky sole",
    },
    {
        "id": "item_044", "name": "Navy Slip-on Sneakers",
        "category": "shoes", "subcategory": "sneakers",
        "color": "navy", "color_family": "cool", "material": "canvas",
        "formality": 1,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["casual", "relaxed", "summer"],
        "notes": "laceless — good for travel",
    },
    {
        "id": "item_045", "name": "Beige Leather Sandals",
        "category": "shoes", "subcategory": "sandals",
        "color": "beige", "color_family": "neutral", "material": "leather",
        "formality": 2,
        "occasions": ["casual", "beach", "dinner"],
        "seasons": ["spring", "summer"],
        "style_tags": ["minimal", "relaxed", "warm-weather"],
        "notes": "two-strap, comfortable for all-day wear",
    },

    # ── ACCESSORIES  item_046 – item_060 ────────────────────────────────────
    {
        "id": "item_046", "name": "Black Leather Belt",
        "category": "accessories", "subcategory": "belt",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual", "job-interview"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "minimal", "essential"],
        "notes": "match to shoes — silver buckle",
    },
    {
        "id": "item_047", "name": "Navy Wool Scarf",
        "category": "accessories", "subcategory": "scarf",
        "color": "navy", "color_family": "cool", "material": "wool",
        "formality": 2,
        "occasions": ["casual", "work", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "preppy", "warm"],
        "notes": "fine gauge — not bulky",
    },
    {
        "id": "item_048", "name": "Camel Leather Watch",
        "category": "accessories", "subcategory": "watch",
        "color": "camel", "color_family": "warm", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual", "job-interview"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "luxe", "minimal"],
        "notes": "36mm case — understated dress watch",
    },
    {
        "id": "item_049", "name": "Black Leather Tote",
        "category": "accessories", "subcategory": "bag",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "professional", "structured"],
        "notes": "fits A4 + laptop, top zip closure",
    },
    {
        "id": "item_050", "name": "Grey Wool Beanie",
        "category": "accessories", "subcategory": "hat",
        "color": "grey", "color_family": "neutral", "material": "wool",
        "formality": 1,
        "occasions": ["casual", "weekend", "gym"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["casual", "basic", "warm"],
        "notes": "no pom — clean look",
    },
    {
        "id": "item_051", "name": "Tortoiseshell Sunglasses",
        "category": "accessories", "subcategory": "sunglasses",
        "color": "tortoiseshell", "color_family": "warm", "material": "acetate",
        "formality": 2,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["retro", "classic", "warm-weather"],
        "notes": "round frame — UV400",
    },
    {
        "id": "item_052", "name": "Black Silk Tie",
        "category": "accessories", "subcategory": "tie",
        "color": "black", "color_family": "neutral", "material": "silk",
        "formality": 5,
        "occasions": ["job-interview", "dinner", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "formal", "sleek"],
        "notes": "plain weave — works for funerals too",
    },
    {
        "id": "item_053", "name": "Navy Silk Pocket Square",
        "category": "accessories", "subcategory": "pocket square",
        "color": "navy", "color_family": "cool", "material": "silk",
        "formality": 4,
        "occasions": ["dinner", "job-interview", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "elegant", "formal"],
        "notes": "TV fold or puff fold",
    },
    {
        "id": "item_054", "name": "Gold Minimal Necklace",
        "category": "accessories", "subcategory": "necklace",
        "color": "gold", "color_family": "warm", "material": "gold-plated",
        "formality": 3,
        "occasions": ["dinner", "smart-casual", "work"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "elegant", "feminine"],
        "notes": "thin chain, delicate — stacks well",
    },
    {
        "id": "item_055", "name": "Brown Leather Weekender",
        "category": "accessories", "subcategory": "bag",
        "color": "brown", "color_family": "warm", "material": "leather",
        "formality": 2,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "rugged", "travel"],
        "notes": "duffle style, fits a weekend's worth",
    },
    {
        "id": "item_056", "name": "Black Leather Gloves",
        "category": "accessories", "subcategory": "gloves",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "elegant", "structured"],
        "notes": "unlined — not for extreme cold",
    },
    {
        "id": "item_057", "name": "Cream Linen Pocket Square",
        "category": "accessories", "subcategory": "pocket square",
        "color": "cream", "color_family": "neutral", "material": "linen",
        "formality": 3,
        "occasions": ["dinner", "smart-casual", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "classic", "clean"],
        "notes": "versatile — pairs with both blazers",
    },
    {
        "id": "item_058", "name": "Silver Hoop Earrings",
        "category": "accessories", "subcategory": "earrings",
        "color": "silver", "color_family": "neutral", "material": "sterling silver",
        "formality": 3,
        "occasions": ["dinner", "work", "casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "classic", "feminine"],
        "notes": "medium hoop — 30mm diameter",
    },
    {
        "id": "item_059", "name": "Navy Baseball Cap",
        "category": "accessories", "subcategory": "hat",
        "color": "navy", "color_family": "cool", "material": "cotton",
        "formality": 1,
        "occasions": ["casual", "weekend", "gym"],
        "seasons": ["spring", "summer"],
        "style_tags": ["casual", "sporty", "basic"],
        "notes": "unstructured, low-profile",
    },
    {
        "id": "item_060", "name": "Olive Canvas Backpack",
        "category": "accessories", "subcategory": "bag",
        "color": "olive", "color_family": "warm", "material": "canvas",
        "formality": 1,
        "occasions": ["casual", "weekend", "work"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["casual", "functional", "earthy"],
        "notes": "15L, fits daily essentials + small laptop",
    },
]


def _assign_dates(items: list[dict]) -> list[dict]:
    """Randomly assign owned_since and last_worn dates using seeded random."""
    result = []
    for item in items:
        days_owned = random.randint(120, 1460)
        owned = BASE_DATE - timedelta(days=days_owned)
        item = {**item, "owned_since": owned.strftime("%Y-%m-%d")}

        if random.random() > 0.15:  # 85% of items have been worn
            days_since = random.randint(1, min(days_owned, 200))
            last = BASE_DATE - timedelta(days=days_since)
            item["last_worn"] = last.strftime("%Y-%m-%d")
        else:
            item["last_worn"] = None

        item["image_path"] = None
        result.append(item)
    return result


# ---------------------------------------------------------------------------
# 50 RAGAS evaluation queries
# ground_truth_ids reference actual item IDs from the wardrobe above.
# ---------------------------------------------------------------------------
EVAL_QUERIES = [
    # ── JOB INTERVIEW (8 queries) ───────────────────────────────────────────
    {
        "query": "job interview at a law firm, autumn morning, London 12°C, smart professional",
        "occasion": "job-interview", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_018", "item_028", "item_037", "item_046", "item_048"],
    },
    {
        "query": "tech startup interview, casual office vibe, spring 18°C",
        "occasion": "job-interview", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_003", "item_019", "item_028", "item_040"],
    },
    {
        "query": "finance internship interview, winter, need to look polished",
        "occasion": "job-interview", "formality": 5,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_021", "item_031", "item_037", "item_052", "item_053"],
    },
    {
        "query": "second-round interview, creative agency, smart-casual dress code, autumn",
        "occasion": "job-interview", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_004", "item_016", "item_028", "item_040"],
    },
    {
        "query": "morning interview, cold and rainy, need coat, formality 4",
        "occasion": "job-interview", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_018", "item_031", "item_037", "item_046"],
    },
    {
        "query": "remote video interview, smart casual, just top half visible",
        "occasion": "job-interview", "formality": 3,
        "expected_categories": ["tops"],
        "ground_truth_ids": ["item_003", "item_015"],
    },
    {
        "query": "interview at consulting firm, strictly formal, winter afternoon",
        "occasion": "job-interview", "formality": 5,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_008", "item_021", "item_028", "item_037", "item_046", "item_052"],
    },
    {
        "query": "final round interview, fashion company, need to show personal style",
        "occasion": "job-interview", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_010", "item_022", "item_034", "item_040", "item_058"],
    },

    # ── FORMAL / SMART DINNER (8 queries) ───────────────────────────────────
    {
        "query": "smart casual dinner date, spring evening, 20°C, restaurant in the city",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_019", "item_040", "item_048"],
    },
    {
        "query": "formal dinner party, winter, suit required, 8°C outside",
        "occasion": "dinner", "formality": 5,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_008", "item_021", "item_031", "item_037", "item_054"],
    },
    {
        "query": "casual dinner with friends, autumn, laid-back bistro, 15°C",
        "occasion": "dinner", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_004", "item_016", "item_043"],
    },
    {
        "query": "date night dinner, rooftop bar, warm summer evening 25°C",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_008", "item_027", "item_045", "item_054"],
    },
    {
        "query": "dinner at a Michelin star restaurant, need to look elegant, autumn",
        "occasion": "dinner", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_010", "item_022", "item_029", "item_040", "item_048"],
    },
    {
        "query": "Sunday lunch, gastropub, relaxed smart casual, spring 16°C",
        "occasion": "dinner", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_012", "item_020", "item_038"],
    },
    {
        "query": "dinner party as a guest, festive winter atmosphere",
        "occasion": "dinner", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_004", "item_018", "item_034", "item_040", "item_057"],
    },
    {
        "query": "outdoor summer dinner, 28°C, dress code is smart-casual",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_006", "item_024", "item_045"],
    },

    # ── WORK / OFFICE (6 queries) ────────────────────────────────────────────
    {
        "query": "regular office day, autumn, meetings in the morning, formality 3",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_003", "item_019", "item_040", "item_049"],
    },
    {
        "query": "client presentation at work, need to look sharp, winter",
        "occasion": "work", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_018", "item_028", "item_037", "item_046"],
    },
    {
        "query": "casual Friday at a creative office, spring, relaxed but professional",
        "occasion": "work", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_002", "item_023", "item_036"],
    },
    {
        "query": "hybrid work day, need an outfit that works for desk and after-work drinks",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_015", "item_021", "item_040", "item_058"],
    },
    {
        "query": "office in winter, heating is broken, need warm but professional layers",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_010", "item_018", "item_028", "item_040"],
    },
    {
        "query": "summer work day, hot office, formality 3, need to stay cool",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_001", "item_020", "item_041"],
    },

    # ── CASUAL / WEEKEND (7 queries) ─────────────────────────────────────────
    {
        "query": "Saturday errands and coffee, spring, relaxed",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_007", "item_016", "item_036"],
    },
    {
        "query": "Sunday walk in the park, autumn, 13°C",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_011", "item_026", "item_032", "item_043"],
    },
    {
        "query": "weekend brunch with friends, summer, nothing too dressed up",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_005", "item_024", "item_044"],
    },
    {
        "query": "casual drinks with colleagues after work, spring evening",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_009", "item_023", "item_036"],
    },
    {
        "query": "winter weekend, staying warm but stylish, city exploring",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_003", "item_017", "item_033", "item_043", "item_047"],
    },
    {
        "query": "very casual Sunday at home, maybe a quick shop run",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_007", "item_026", "item_039"],
    },
    {
        "query": "autumn market trip, light layers, comfortable walking",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_013", "item_016", "item_035", "item_043"],
    },

    # ── GYM / ACTIVE (5 queries) ─────────────────────────────────────────────
    {
        "query": "morning gym session, weight training",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_011", "item_025", "item_042"],
    },
    {
        "query": "outdoor run, spring morning, 10°C",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_007", "item_026", "item_042"],
    },
    {
        "query": "yoga class followed by errands",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_014", "item_026", "item_036"],
    },
    {
        "query": "gym warm-up and cardio, winter, cold outside",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_007", "item_025", "item_033", "item_042"],
    },
    {
        "query": "casual sports with friends, park, summer afternoon",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_014", "item_025", "item_039"],
    },

    # ── WEDDING GUEST (5 queries) ────────────────────────────────────────────
    {
        "query": "afternoon wedding, summer garden party, formal dress code, 24°C",
        "occasion": "wedding-guest", "formality": 4,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_008", "item_021", "item_037", "item_054"],
    },
    {
        "query": "evening wedding reception, autumn, black tie optional",
        "occasion": "wedding-guest", "formality": 5,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_008", "item_021", "item_034", "item_037", "item_052"],
    },
    {
        "query": "outdoor barn wedding, spring, smart-casual dress code",
        "occasion": "wedding-guest", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_010", "item_027", "item_029", "item_038", "item_058"],
    },
    {
        "query": "civil ceremony wedding, intimate and relaxed, summer",
        "occasion": "wedding-guest", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_022", "item_041", "item_057"],
    },
    {
        "query": "winter wedding, church ceremony, need to be warm and elegant",
        "occasion": "wedding-guest", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_008", "item_021", "item_031", "item_037", "item_056"],
    },

    # ── BEACH / SUMMER (4 queries) ───────────────────────────────────────────
    {
        "query": "beach day, hot summer, 32°C, just hanging by the sea",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_014", "item_024", "item_044"],
    },
    {
        "query": "seaside lunch, summer, warm but breezy, casual",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_006", "item_024", "item_045", "item_051"],
    },
    {
        "query": "beach holiday, relaxed days, packing light",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_005", "item_024", "item_039"],
    },
    {
        "query": "boat trip, sunny, need to stay cool and casual, summer",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_005", "item_025", "item_044", "item_051"],
    },

    # ── SMART CASUAL MIXED (7 queries) ──────────────────────────────────────
    {
        "query": "art gallery opening, smart-casual, autumn evening",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_004", "item_022", "item_034", "item_040"],
    },
    {
        "query": "theatre show, smart casual, winter evening",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_010", "item_017", "item_029", "item_040", "item_048"],
    },
    {
        "query": "catching up with an old friend, nice cafe, spring lunch",
        "occasion": "smart-casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_012", "item_016", "item_036"],
    },
    {
        "query": "book launch event, creative crowd, autumn",
        "occasion": "smart-casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_013", "item_017", "item_030", "item_036"],
    },
    {
        "query": "networking event at a nice venue, winter, want to stand out slightly",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_015", "item_021", "item_034", "item_040", "item_058"],
    },
    {
        "query": "birthday dinner at a lively restaurant, casual feel but effortful, spring",
        "occasion": "smart-casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_009", "item_023", "item_043"],
    },
    {
        "query": "drinks at a rooftop bar after work, summer, need to go straight from office",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_020", "item_041", "item_048"],
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(os.path.join("data", "seed"), exist_ok=True)
    os.makedirs(os.path.join("data", "eval"), exist_ok=True)

    items = _assign_dates(ITEMS_RAW)

    with open(OUT_ITEMS, "w") as f:
        json.dump(items, f, indent=2)
    print(f"Wrote {len(items)} items → {OUT_ITEMS}")

    # Validate all ground_truth_ids exist
    item_ids = {i["id"] for i in items}
    for q in EVAL_QUERIES:
        missing = [x for x in q["ground_truth_ids"] if x not in item_ids]
        if missing:
            print(f"  WARNING: query '{q['query'][:50]}' references unknown ids: {missing}")

    with open(OUT_EVAL, "w") as f:
        json.dump(EVAL_QUERIES, f, indent=2)
    print(f"Wrote {len(EVAL_QUERIES)} eval queries → {OUT_EVAL}")

    # Category summary
    from collections import Counter
    cats = Counter(i["category"] for i in items)
    print("\nWardrobe breakdown:")
    for cat, n in sorted(cats.items()):
        print(f"  {cat:15s} {n}")


if __name__ == "__main__":
    main()
