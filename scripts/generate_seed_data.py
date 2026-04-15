"""
Generate synthetic wardrobe data for development.

random.seed(42) ensures full reproducibility.

Outputs:
  data/seed/wardrobe_items.json   - 60 wardrobe items (women's, diverse styles)
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
# Diverse women's wardrobe: casual to black-tie, various styles and seasons.
# Dresses use subcategory="dress" within category="tops"; the outfit agent
# is instructed to treat a dress as covering top + bottom.
# Dates are assigned after definition using seeded random.
# ---------------------------------------------------------------------------
ITEMS_RAW = [
    # ── TOPS  item_001 – item_015 ───────────────────────────────────────────
    {
        "id": "item_001", "name": "White Silk Blouse",
        "category": "tops", "subcategory": "blouse",
        "color": "white", "color_family": "neutral", "material": "silk",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual", "job-interview"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["classic", "elegant", "feminine"],
        "notes": "slightly oversized, tuck into high-waist bottoms",
    },
    {
        "id": "item_002", "name": "Black Fitted Turtleneck",
        "category": "tops", "subcategory": "turtleneck",
        "color": "black", "color_family": "neutral", "material": "wool-blend",
        "formality": 3,
        "occasions": ["dinner", "work", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["minimal", "classic", "sleek"],
        "notes": "slim fit — the foundation of a monochrome look",
    },
    {
        "id": "item_003", "name": "Ivory Cashmere Sweater",
        "category": "tops", "subcategory": "sweater",
        "color": "ivory", "color_family": "neutral", "material": "cashmere",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter", "spring"],
        "style_tags": ["luxe", "minimal", "classic"],
        "notes": "crew neck, relaxed fit — hand wash only",
    },
    {
        "id": "item_004", "name": "Striped Breton Top",
        "category": "tops", "subcategory": "t-shirt",
        "color": "navy/white", "color_family": "cool", "material": "cotton",
        "formality": 1,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["nautical", "casual", "french"],
        "notes": "classic navy stripes, slightly cropped",
    },
    {
        "id": "item_005", "name": "Cream Ribbed Knit Tank",
        "category": "tops", "subcategory": "tank",
        "color": "cream", "color_family": "neutral", "material": "cotton-rib",
        "formality": 2,
        "occasions": ["casual", "dinner", "smart-casual"],
        "seasons": ["spring", "summer"],
        "style_tags": ["minimal", "clean", "versatile"],
        "notes": "pairs well with high-waist skirts or trousers",
    },
    {
        "id": "item_006", "name": "Burgundy Wrap Blouse",
        "category": "tops", "subcategory": "blouse",
        "color": "burgundy", "color_family": "warm", "material": "viscose",
        "formality": 3,
        "occasions": ["dinner", "work", "smart-casual", "wedding-guest"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["feminine", "relaxed", "warm"],
        "notes": "adjustable tie — flattering on all body types",
    },
    {
        "id": "item_007", "name": "Camel Knit Cardigan",
        "category": "tops", "subcategory": "cardigan",
        "color": "camel", "color_family": "warm", "material": "wool-blend",
        "formality": 2,
        "occasions": ["casual", "smart-casual", "work"],
        "seasons": ["autumn", "winter", "spring"],
        "style_tags": ["relaxed", "warm", "layering"],
        "notes": "long open-front style — layer over blouses or tees",
    },
    {
        "id": "item_008", "name": "White Cotton Tee",
        "category": "tops", "subcategory": "t-shirt",
        "color": "white", "color_family": "neutral", "material": "cotton",
        "formality": 1,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["basic", "minimal", "essential"],
        "notes": "slightly oversized, crew neck — the perfect blank canvas",
    },
    {
        "id": "item_009", "name": "Pale Pink Silk Camisole",
        "category": "tops", "subcategory": "camisole",
        "color": "pale pink", "color_family": "warm", "material": "silk",
        "formality": 4,
        "occasions": ["dinner", "wedding-guest", "smart-casual"],
        "seasons": ["spring", "summer"],
        "style_tags": ["feminine", "elegant", "delicate"],
        "notes": "adjustable straps — layer under blazer for work",
    },
    {
        "id": "item_010", "name": "Navy Fine-Knit Jumper",
        "category": "tops", "subcategory": "sweater",
        "color": "navy", "color_family": "cool", "material": "merino wool",
        "formality": 3,
        "occasions": ["work", "smart-casual", "dinner"],
        "seasons": ["autumn", "winter", "spring"],
        "style_tags": ["classic", "preppy", "smart"],
        "notes": "V-neck — tuck into tailored trousers for polish",
    },
    {
        "id": "item_011", "name": "Olive Linen Shirt",
        "category": "tops", "subcategory": "shirt",
        "color": "olive", "color_family": "warm", "material": "linen",
        "formality": 2,
        "occasions": ["casual", "smart-casual", "weekend"],
        "seasons": ["spring", "summer"],
        "style_tags": ["earthy", "relaxed", "casual"],
        "notes": "oversized fit — wear open over a tank or tied at the waist",
    },
    {
        "id": "item_012", "name": "Black Satin Slip Dress",
        "category": "tops", "subcategory": "dress",
        "color": "black", "color_family": "neutral", "material": "satin",
        "formality": 4,
        "occasions": ["dinner", "wedding-guest", "smart-casual"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["elegant", "minimal", "evening"],
        "notes": "midi length — wear alone or layer under a blazer or knit",
    },
    {
        "id": "item_013", "name": "Grey Marl Sweatshirt",
        "category": "tops", "subcategory": "sweatshirt",
        "color": "grey", "color_family": "neutral", "material": "cotton-fleece",
        "formality": 1,
        "occasions": ["casual", "weekend", "gym"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["casual", "comfort", "basic"],
        "notes": "classic crew neck — goes with everything for weekend errands",
    },
    {
        "id": "item_014", "name": "Terracotta Linen Shirt",
        "category": "tops", "subcategory": "shirt",
        "color": "rust", "color_family": "warm", "material": "linen",
        "formality": 2,
        "occasions": ["casual", "smart-casual", "dinner"],
        "seasons": ["spring", "summer"],
        "style_tags": ["earthy", "relaxed", "bohemian"],
        "notes": "slightly oversized with subtle texture — pairs with white or navy",
    },
    {
        "id": "item_015", "name": "Navy Wrap Dress",
        "category": "tops", "subcategory": "dress",
        "color": "navy", "color_family": "cool", "material": "jersey",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["classic", "feminine", "versatile"],
        "notes": "knee length — cinched waist, works for office and evening",
    },

    # ── BOTTOMS  item_016 – item_026 ────────────────────────────────────────
    {
        "id": "item_016", "name": "Dark Indigo Straight Jeans",
        "category": "bottoms", "subcategory": "jeans",
        "color": "dark indigo", "color_family": "cool", "material": "denim",
        "formality": 2,
        "occasions": ["casual", "weekend", "smart-casual", "dinner"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "versatile", "casual"],
        "notes": "straight cut, mid-rise — the most versatile jeans in the wardrobe",
    },
    {
        "id": "item_017", "name": "Black High-Waist Trousers",
        "category": "bottoms", "subcategory": "trousers",
        "color": "black", "color_family": "neutral", "material": "polyester-blend",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["tailored", "classic", "formal"],
        "notes": "wide leg, high rise — looks sharp with a tucked blouse",
    },
    {
        "id": "item_018", "name": "Camel Wide-Leg Trousers",
        "category": "bottoms", "subcategory": "trousers",
        "color": "camel", "color_family": "warm", "material": "wool-blend",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["editorial", "relaxed", "warm"],
        "notes": "high waist — pairs beautifully with ivory or black tops",
    },
    {
        "id": "item_019", "name": "White Linen Wide-Leg Pants",
        "category": "bottoms", "subcategory": "trousers",
        "color": "white", "color_family": "neutral", "material": "linen",
        "formality": 2,
        "occasions": ["casual", "beach", "dinner"],
        "seasons": ["spring", "summer"],
        "style_tags": ["minimal", "summer", "relaxed"],
        "notes": "flowy and breathable — great for warm weather dinners",
    },
    {
        "id": "item_020", "name": "Navy Midi Skirt",
        "category": "bottoms", "subcategory": "skirt",
        "color": "navy", "color_family": "cool", "material": "wool-blend",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter", "spring"],
        "style_tags": ["classic", "polished", "feminine"],
        "notes": "A-line midi — pairs with blouses or tucked turtlenecks",
    },
    {
        "id": "item_021", "name": "Rust Midi Wrap Skirt",
        "category": "bottoms", "subcategory": "skirt",
        "color": "rust", "color_family": "warm", "material": "viscose",
        "formality": 3,
        "occasions": ["dinner", "work", "smart-casual"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["feminine", "bohemian", "warm"],
        "notes": "bias cut, very flattering — tuck in a fitted top",
    },
    {
        "id": "item_022", "name": "Black Tailored Mini Skirt",
        "category": "bottoms", "subcategory": "skirt",
        "color": "black", "color_family": "neutral", "material": "cotton-blend",
        "formality": 2,
        "occasions": ["casual", "dinner", "smart-casual"],
        "seasons": ["spring", "summer"],
        "style_tags": ["chic", "classic", "minimal"],
        "notes": "above the knee — structured waistband, side zip",
    },
    {
        "id": "item_023", "name": "Cream Pleated Midi Skirt",
        "category": "bottoms", "subcategory": "skirt",
        "color": "cream", "color_family": "neutral", "material": "satin",
        "formality": 4,
        "occasions": ["dinner", "wedding-guest", "job-interview"],
        "seasons": ["spring", "summer"],
        "style_tags": ["elegant", "feminine", "formal"],
        "notes": "tea-length pleats — pairs with camisoles or fitted tops",
    },
    {
        "id": "item_024", "name": "Dark Green Tailored Trousers",
        "category": "bottoms", "subcategory": "trousers",
        "color": "dark green", "color_family": "warm", "material": "wool-blend",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["statement", "classic", "earthy"],
        "notes": "straight cut — keep rest of outfit neutral to let these shine",
    },
    {
        "id": "item_025", "name": "Grey Marl Leggings",
        "category": "bottoms", "subcategory": "leggings",
        "color": "grey", "color_family": "neutral", "material": "cotton-blend",
        "formality": 1,
        "occasions": ["gym", "casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["athletic", "comfort", "casual"],
        "notes": "high-waist, moisture-wicking — gym only",
    },
    {
        "id": "item_026", "name": "Black Athletic Shorts",
        "category": "bottoms", "subcategory": "shorts",
        "color": "black", "color_family": "neutral", "material": "polyester",
        "formality": 1,
        "occasions": ["gym"],
        "seasons": ["spring", "summer"],
        "style_tags": ["athletic", "functional", "basic"],
        "notes": "4-inch inseam, moisture-wicking",
    },

    # ── OUTERWEAR  item_027 – item_034 ──────────────────────────────────────
    {
        "id": "item_027", "name": "Camel Trench Coat",
        "category": "outerwear", "subcategory": "trench coat",
        "color": "camel", "color_family": "warm", "material": "cotton",
        "formality": 4,
        "occasions": ["work", "dinner", "smart-casual", "job-interview"],
        "seasons": ["autumn", "winter", "spring"],
        "style_tags": ["classic", "timeless", "elegant"],
        "notes": "belted, water-resistant shell — the wardrobe anchor",
    },
    {
        "id": "item_028", "name": "Black Leather Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 2,
        "occasions": ["casual", "dinner", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["edgy", "cool", "statement"],
        "notes": "cropped moto-style — elevates a simple tee-and-jeans combo",
    },
    {
        "id": "item_029", "name": "Navy Blazer",
        "category": "outerwear", "subcategory": "blazer",
        "color": "navy", "color_family": "cool", "material": "wool-blend",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview", "wedding-guest", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "tailored", "versatile"],
        "notes": "single-breasted, slightly oversized — dress up or down",
    },
    {
        "id": "item_030", "name": "Cream Oversized Blazer",
        "category": "outerwear", "subcategory": "blazer",
        "color": "cream", "color_family": "neutral", "material": "linen-blend",
        "formality": 3,
        "occasions": ["smart-casual", "casual", "dinner"],
        "seasons": ["spring", "summer"],
        "style_tags": ["editorial", "relaxed", "minimal"],
        "notes": "slouchy fit — pair with jeans or a slip skirt",
    },
    {
        "id": "item_031", "name": "Charcoal Wool Coat",
        "category": "outerwear", "subcategory": "coat",
        "color": "charcoal", "color_family": "neutral", "material": "wool",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "minimal", "formal"],
        "notes": "double-breasted, below-knee — extremely versatile",
    },
    {
        "id": "item_032", "name": "Olive Utility Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "olive", "color_family": "warm", "material": "cotton",
        "formality": 2,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "autumn"],
        "style_tags": ["casual", "utilitarian", "earthy"],
        "notes": "multiple pockets — works with jeans or midi skirts",
    },
    {
        "id": "item_033", "name": "Light Grey Puffer Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "light grey", "color_family": "neutral", "material": "nylon",
        "formality": 1,
        "occasions": ["casual", "gym", "weekend"],
        "seasons": ["winter"],
        "style_tags": ["casual", "functional", "warm"],
        "notes": "packable 650-fill down — warm without bulk",
    },
    {
        "id": "item_034", "name": "Burgundy Bouclé Jacket",
        "category": "outerwear", "subcategory": "jacket",
        "color": "burgundy", "color_family": "warm", "material": "bouclé wool",
        "formality": 4,
        "occasions": ["work", "dinner", "wedding-guest"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["statement", "textured", "feminine"],
        "notes": "collarless, cropped — pairs with black trousers or a midi skirt",
    },

    # ── SHOES  item_035 – item_044 ──────────────────────────────────────────
    {
        "id": "item_035", "name": "White Leather Trainers",
        "category": "shoes", "subcategory": "sneakers",
        "color": "white", "color_family": "neutral", "material": "leather",
        "formality": 1,
        "occasions": ["casual", "weekend"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["minimal", "clean", "versatile"],
        "notes": "classic low-profile — keep very clean for best effect",
    },
    {
        "id": "item_036", "name": "Black Block-Heel Pumps",
        "category": "shoes", "subcategory": "heels",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "elegant", "formal"],
        "notes": "60mm block heel — comfortable enough for full-day wear",
    },
    {
        "id": "item_037", "name": "Tan Leather Loafers",
        "category": "shoes", "subcategory": "loafers",
        "color": "tan", "color_family": "warm", "material": "leather",
        "formality": 3,
        "occasions": ["work", "smart-casual", "dinner"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["preppy", "smart", "classic"],
        "notes": "penny loafer — no socks in summer for a relaxed look",
    },
    {
        "id": "item_038", "name": "Black Chelsea Boots",
        "category": "shoes", "subcategory": "chelsea boots",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "versatile", "smart"],
        "notes": "elastic gusset, ankle height — pairs with almost everything",
    },
    {
        "id": "item_039", "name": "Nude Block-Heel Sandals",
        "category": "shoes", "subcategory": "sandals",
        "color": "beige", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["dinner", "smart-casual", "wedding-guest"],
        "seasons": ["spring", "summer"],
        "style_tags": ["feminine", "elegant", "minimal"],
        "notes": "ankle strap — nude elongates the leg",
    },
    {
        "id": "item_040", "name": "White Canvas Sneakers",
        "category": "shoes", "subcategory": "sneakers",
        "color": "white", "color_family": "neutral", "material": "canvas",
        "formality": 1,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["casual", "basic", "summer"],
        "notes": "machine washable — keep pristine",
    },
    {
        "id": "item_041", "name": "Black Leather Ankle Boots",
        "category": "shoes", "subcategory": "boots",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 2,
        "occasions": ["casual", "dinner", "weekend"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["chic", "versatile", "edgy"],
        "notes": "flat, pointed toe — looks great with skirts and jeans",
    },
    {
        "id": "item_042", "name": "Tan Suede Mules",
        "category": "shoes", "subcategory": "mules",
        "color": "tan", "color_family": "warm", "material": "suede",
        "formality": 2,
        "occasions": ["casual", "smart-casual", "dinner"],
        "seasons": ["spring", "summer"],
        "style_tags": ["relaxed", "minimal", "warm-weather"],
        "notes": "low heel — avoid in wet weather",
    },
    {
        "id": "item_043", "name": "Silver Strappy Heels",
        "category": "shoes", "subcategory": "heels",
        "color": "silver", "color_family": "neutral", "material": "metallic leather",
        "formality": 5,
        "occasions": ["dinner", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["glamorous", "evening", "statement"],
        "notes": "stiletto heel — goes with almost any colour dress",
    },
    {
        "id": "item_044", "name": "Brown Suede Knee Boots",
        "category": "shoes", "subcategory": "boots",
        "color": "brown", "color_family": "warm", "material": "suede",
        "formality": 3,
        "occasions": ["casual", "smart-casual", "dinner"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "warm", "feminine"],
        "notes": "flat — pairs with midi skirts and straight jeans",
    },

    # ── ACCESSORIES  item_045 – item_060 ────────────────────────────────────
    {
        "id": "item_045", "name": "Black Leather Tote",
        "category": "accessories", "subcategory": "bag",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["professional", "structured", "minimal"],
        "notes": "fits laptop and A4 — the work-week essential",
    },
    {
        "id": "item_046", "name": "Tan Mini Shoulder Bag",
        "category": "accessories", "subcategory": "bag",
        "color": "tan", "color_family": "warm", "material": "leather",
        "formality": 2,
        "occasions": ["casual", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn"],
        "style_tags": ["chic", "minimal", "casual"],
        "notes": "adjustable chain strap — doubles as crossbody",
    },
    {
        "id": "item_047", "name": "Cream Leather Clutch",
        "category": "accessories", "subcategory": "bag",
        "color": "cream", "color_family": "neutral", "material": "leather",
        "formality": 4,
        "occasions": ["dinner", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["elegant", "formal", "evening"],
        "notes": "envelope style — fits phone, cards and keys",
    },
    {
        "id": "item_048", "name": "Black Mini Crossbody Bag",
        "category": "accessories", "subcategory": "bag",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 2,
        "occasions": ["casual", "dinner", "weekend"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "practical", "classic"],
        "notes": "compact — perfect for evenings and errands",
    },
    {
        "id": "item_049", "name": "Black Leather Belt",
        "category": "accessories", "subcategory": "belt",
        "color": "black", "color_family": "neutral", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual", "job-interview"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "minimal", "essential"],
        "notes": "slim 2cm width — gold buckle, match to jewellery tone",
    },
    {
        "id": "item_050", "name": "Gold Chain Necklace",
        "category": "accessories", "subcategory": "necklace",
        "color": "gold", "color_family": "warm", "material": "gold-plated",
        "formality": 3,
        "occasions": ["dinner", "work", "smart-casual", "casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "elegant", "versatile"],
        "notes": "medium-weight chain, 45cm — stacks beautifully",
    },
    {
        "id": "item_051", "name": "Pearl Stud Earrings",
        "category": "accessories", "subcategory": "earrings",
        "color": "white", "color_family": "neutral", "material": "freshwater pearl",
        "formality": 4,
        "occasions": ["work", "dinner", "job-interview", "wedding-guest"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "elegant", "timeless"],
        "notes": "6mm pearl — the most polished everyday earring",
    },
    {
        "id": "item_052", "name": "Gold Hoop Earrings",
        "category": "accessories", "subcategory": "earrings",
        "color": "gold", "color_family": "warm", "material": "gold-plated",
        "formality": 2,
        "occasions": ["casual", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "classic", "everyday"],
        "notes": "25mm hoop — the everyday earring staple",
    },
    {
        "id": "item_053", "name": "Silver Layered Necklace",
        "category": "accessories", "subcategory": "necklace",
        "color": "silver", "color_family": "neutral", "material": "sterling silver",
        "formality": 3,
        "occasions": ["dinner", "casual", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "delicate", "modern"],
        "notes": "two-chain layered pendant set — looks effortless",
    },
    {
        "id": "item_054", "name": "Navy Wool Scarf",
        "category": "accessories", "subcategory": "scarf",
        "color": "navy", "color_family": "cool", "material": "wool",
        "formality": 2,
        "occasions": ["casual", "work", "smart-casual"],
        "seasons": ["autumn", "winter"],
        "style_tags": ["classic", "preppy", "warm"],
        "notes": "fine gauge — not bulky under a coat collar",
    },
    {
        "id": "item_055", "name": "Tortoiseshell Sunglasses",
        "category": "accessories", "subcategory": "sunglasses",
        "color": "tortoiseshell", "color_family": "warm", "material": "acetate",
        "formality": 2,
        "occasions": ["casual", "weekend", "beach"],
        "seasons": ["spring", "summer"],
        "style_tags": ["retro", "classic", "warm-weather"],
        "notes": "cat-eye frame — UV400 lenses",
    },
    {
        "id": "item_056", "name": "Camel Leather Watch",
        "category": "accessories", "subcategory": "watch",
        "color": "camel", "color_family": "warm", "material": "leather",
        "formality": 3,
        "occasions": ["work", "dinner", "smart-casual", "job-interview"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["classic", "minimal", "luxe"],
        "notes": "32mm case — understated dress watch",
    },
    {
        "id": "item_057", "name": "Silver Chain Bracelet",
        "category": "accessories", "subcategory": "bracelet",
        "color": "silver", "color_family": "neutral", "material": "sterling silver",
        "formality": 2,
        "occasions": ["casual", "dinner", "smart-casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "delicate", "everyday"],
        "notes": "adjustable box chain — stacks with a watch",
    },
    {
        "id": "item_058", "name": "Silver Hoop Earrings",
        "category": "accessories", "subcategory": "earrings",
        "color": "silver", "color_family": "neutral", "material": "sterling silver",
        "formality": 3,
        "occasions": ["dinner", "work", "casual"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["minimal", "classic", "versatile"],
        "notes": "35mm hoop — bold but minimal",
    },
    {
        "id": "item_059", "name": "Champagne Silk Hair Scarf",
        "category": "accessories", "subcategory": "scarf",
        "color": "ivory", "color_family": "neutral", "material": "silk",
        "formality": 3,
        "occasions": ["dinner", "smart-casual", "casual"],
        "seasons": ["spring", "summer"],
        "style_tags": ["elegant", "feminine", "retro"],
        "notes": "wear in hair, around neck, or tied on a bag handle",
    },
    {
        "id": "item_060", "name": "Black Running Trainers",
        "category": "shoes", "subcategory": "sneakers",
        "color": "black", "color_family": "neutral", "material": "synthetic",
        "formality": 1,
        "occasions": ["gym"],
        "seasons": ["spring", "summer", "autumn", "winter"],
        "style_tags": ["athletic", "functional"],
        "notes": "dedicated to running only — cushioned sole",
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
        "ground_truth_ids": ["item_001", "item_017", "item_029", "item_036", "item_049", "item_051"],
    },
    {
        "query": "tech startup interview, casual office vibe, spring 18°C",
        "occasion": "job-interview", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_003", "item_018", "item_029", "item_038"],
    },
    {
        "query": "finance internship interview, winter, need to look polished",
        "occasion": "job-interview", "formality": 5,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_017", "item_031", "item_036", "item_051"],
    },
    {
        "query": "second-round interview, creative agency, smart-casual dress code, autumn",
        "occasion": "job-interview", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_002", "item_016", "item_029", "item_038"],
    },
    {
        "query": "morning interview, cold and rainy, need coat, formality 4",
        "occasion": "job-interview", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_017", "item_031", "item_036", "item_049"],
    },
    {
        "query": "remote video interview, smart casual, just top half visible",
        "occasion": "job-interview", "formality": 3,
        "expected_categories": ["tops"],
        "ground_truth_ids": ["item_001", "item_003", "item_010"],
    },
    {
        "query": "panel interview at a prestigious consultancy, formality 5",
        "occasion": "job-interview", "formality": 5,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_001", "item_017", "item_029", "item_036"],
    },
    {
        "query": "graduate scheme interview, neutral palette, London autumn",
        "occasion": "job-interview", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_001", "item_017", "item_027", "item_036"],
    },

    # ── DINNER / DATE (10 queries) ──────────────────────────────────────────
    {
        "query": "romantic dinner, smart casual, spring evening",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_006", "item_021", "item_039", "item_052"],
    },
    {
        "query": "birthday dinner at a nice restaurant, autumn, warm tones",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_006", "item_021", "item_027", "item_038"],
    },
    {
        "query": "dinner with partner's family, want to look put-together but not overdressed",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_003", "item_020", "item_037", "item_050"],
    },
    {
        "query": "first date dinner, going for effortlessly chic, summer",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_005", "item_022", "item_039"],
    },
    {
        "query": "black-tie optional gala dinner, formal, summer evening",
        "occasion": "dinner", "formality": 5,
        "expected_categories": ["tops", "shoes", "accessories"],
        "ground_truth_ids": ["item_012", "item_043", "item_047", "item_051"],
    },
    {
        "query": "sushi dinner, casual, mid-week, nothing too fancy",
        "occasion": "dinner", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_004", "item_016", "item_041"],
    },
    {
        "query": "wine bar with girlfriends, autumn, statement jacket vibes",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_005", "item_016", "item_028", "item_041"],
    },
    {
        "query": "Michelin star restaurant, smart formal, winter",
        "occasion": "dinner", "formality": 4,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_012", "item_017", "item_036", "item_050"],
    },
    {
        "query": "outdoor dinner party, summer evening, could get chilly",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_009", "item_021", "item_030", "item_039"],
    },
    {
        "query": "dinner date, minimal aesthetic, cool tones, autumn",
        "occasion": "dinner", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_002", "item_020", "item_038", "item_053"],
    },

    # ── WORK / OFFICE (8 queries) ───────────────────────────────────────────
    {
        "query": "regular office day, business casual, autumn",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_003", "item_018", "item_037"],
    },
    {
        "query": "client meeting at work, need to look sharp, winter",
        "occasion": "work", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_017", "item_031", "item_036", "item_056"],
    },
    {
        "query": "casual Friday at the office, smart but relaxed, spring",
        "occasion": "work", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_011", "item_016", "item_037"],
    },
    {
        "query": "creative office environment, expressive style, autumn",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_006", "item_024", "item_038"],
    },
    {
        "query": "work from home, comfortable but put-together for video calls",
        "occasion": "work", "formality": 2,
        "expected_categories": ["tops"],
        "ground_truth_ids": ["item_003", "item_007", "item_010"],
    },
    {
        "query": "all-day conference, need professional look, comfortable shoes",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_001", "item_020", "item_037", "item_045"],
    },
    {
        "query": "board presentation, formal office setting, winter",
        "occasion": "work", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_001", "item_017", "item_029", "item_036"],
    },
    {
        "query": "networking event after work, smart evening look",
        "occasion": "work", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_015", "item_036", "item_050", "item_051"],
    },

    # ── CASUAL / WEEKEND (8 queries) ────────────────────────────────────────
    {
        "query": "weekend brunch, relaxed, spring sunshine",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_004", "item_016", "item_035"],
    },
    {
        "query": "farmers market, comfortable, earthy tones, autumn",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_011", "item_016", "item_041"],
    },
    {
        "query": "art gallery visit, casual chic, minimal aesthetic",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_002", "item_022", "item_038", "item_050"],
    },
    {
        "query": "shopping trip, comfortable and stylish, summer",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_008", "item_016", "item_035"],
    },
    {
        "query": "park picnic with friends, sunny spring day",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_004", "item_019", "item_040", "item_055"],
    },
    {
        "query": "coffee date, casual and cute, autumn afternoon",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_007", "item_021", "item_038"],
    },
    {
        "query": "Sunday errands, cosy and warm, winter",
        "occasion": "casual", "formality": 1,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_013", "item_016", "item_033", "item_041"],
    },
    {
        "query": "cinema date, relaxed evening look, autumn",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_007", "item_016", "item_041"],
    },

    # ── WEDDING GUEST (6 queries) ────────────────────────────────────────────
    {
        "query": "summer wedding, outdoor ceremony, feminine and floral",
        "occasion": "wedding-guest", "formality": 4,
        "expected_categories": ["tops", "shoes", "accessories"],
        "ground_truth_ids": ["item_012", "item_043", "item_047", "item_051"],
    },
    {
        "query": "autumn wedding, church ceremony, elegant and warm",
        "occasion": "wedding-guest", "formality": 4,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_009", "item_023", "item_034", "item_036"],
    },
    {
        "query": "intimate wedding, garden party, pastel palette, spring",
        "occasion": "wedding-guest", "formality": 4,
        "expected_categories": ["tops", "shoes", "accessories"],
        "ground_truth_ids": ["item_015", "item_039", "item_047"],
    },
    {
        "query": "black tie optional winter wedding, need coat",
        "occasion": "wedding-guest", "formality": 5,
        "expected_categories": ["tops", "outerwear", "shoes", "accessories"],
        "ground_truth_ids": ["item_012", "item_031", "item_043", "item_047"],
    },
    {
        "query": "casual beach wedding, summer, relaxed dressy",
        "occasion": "wedding-guest", "formality": 3,
        "expected_categories": ["tops", "shoes", "accessories"],
        "ground_truth_ids": ["item_015", "item_039", "item_052"],
    },
    {
        "query": "evening wedding reception, cocktail attire, bold accessories",
        "occasion": "wedding-guest", "formality": 4,
        "expected_categories": ["tops", "shoes", "accessories"],
        "ground_truth_ids": ["item_012", "item_036", "item_050", "item_051"],
    },

    # ── GYM / ACTIVE (4 queries) ─────────────────────────────────────────────
    {
        "query": "morning gym session, functional and comfortable",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_013", "item_025", "item_060"],
    },
    {
        "query": "outdoor run followed by coffee, athleisure",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_013", "item_025", "item_060"],
    },
    {
        "query": "yoga class, comfortable and breathable",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms"],
        "ground_truth_ids": ["item_013", "item_025"],
    },
    {
        "query": "gym to brunch, need to go from athletic to casual",
        "occasion": "gym", "formality": 1,
        "expected_categories": ["tops", "bottoms", "shoes", "outerwear"],
        "ground_truth_ids": ["item_013", "item_025", "item_035", "item_032"],
    },

    # ── SMART CASUAL / MIXED (6 queries) ────────────────────────────────────
    {
        "query": "smart casual drinks party, autumn evening, sophisticated",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_006", "item_020", "item_038", "item_050"],
    },
    {
        "query": "gallery opening, smart casual, minimalist aesthetic",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_002", "item_017", "item_036"],
    },
    {
        "query": "hen party brunch, fun and polished, summer",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes", "accessories"],
        "ground_truth_ids": ["item_009", "item_021", "item_039", "item_052"],
    },
    {
        "query": "theatre night, smart casual, autumn, need layers",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "outerwear", "shoes"],
        "ground_truth_ids": ["item_010", "item_020", "item_027", "item_038"],
    },
    {
        "query": "press event, editorial looks, minimal colour palette",
        "occasion": "smart-casual", "formality": 3,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_002", "item_022", "item_036"],
    },
    {
        "query": "house party, casual chic, want to stand out",
        "occasion": "casual", "formality": 2,
        "expected_categories": ["tops", "bottoms", "shoes"],
        "ground_truth_ids": ["item_006", "item_016", "item_041"],
    },
]


# ---------------------------------------------------------------------------
# Build & save
# ---------------------------------------------------------------------------
def _build_items() -> list[dict]:
    items = _assign_dates(ITEMS_RAW)
    for idx, item in enumerate(items, start=1):
        item["item_id"] = item.pop("id")
        item["wear_count"] = random.randint(0, 30)
    return items


def main() -> None:
    os.makedirs(os.path.dirname(OUT_ITEMS), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_EVAL), exist_ok=True)

    items = _build_items()
    with open(OUT_ITEMS, "w") as f:
        json.dump(items, f, indent=2)
    print(f"Wrote {len(items)} items -> {OUT_ITEMS}")

    with open(OUT_EVAL, "w") as f:
        json.dump(EVAL_QUERIES, f, indent=2)
    print(f"Wrote {len(EVAL_QUERIES)} eval queries -> {OUT_EVAL}")


if __name__ == "__main__":
    main()
