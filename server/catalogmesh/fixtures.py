"""Authored development examples, not independent commercial benchmark data."""

# Concept keys build fixture annotations only. They are never sent to Laya or retrieval.
CONCEPTS = [
    (
        "earbuds",
        "Wireless earbuds",
        "Complete wireless in-ear headphones, including sets with charging cases.",
    ),
    (
        "chargecase",
        "Earbud charging cases",
        "Replacement electronic charging cases for earbuds. Earbuds not included.",
    ),
    (
        "cover",
        "Protective earbud case covers",
        "Non-electronic protective shells and covers for earbud charging cases.",
    ),
    (
        "tips",
        "Earbud cushions & tips",
        "Replacement silicone ear tips and ear cushions for headphones.",
    ),
    (
        "dock",
        "Laptop docking stations",
        "USB-C docks and hubs connecting monitors, peripherals and laptop power.",
    ),
    (
        "charger",
        "USB power adapters",
        "USB-C wall chargers and power supplies. Not docking stations.",
    ),
    ("grinder", "Coffee grinders", "Appliances grinding coffee beans. Do not brew coffee."),
    ("espresso", "Espresso machines", "Machines that brew espresso coffee with pressure."),
    (
        "descaler",
        "Coffee machine cleaners",
        "Descaling liquids and cleaning tablets for coffee appliances.",
    ),
    ("vacuum", "Robot vacuum cleaners", "Complete autonomous floor-cleaning vacuum robots."),
    (
        "filter",
        "Vacuum filters",
        "Replacement HEPA filters for vacuum cleaners. Not complete vacuums.",
    ),
    (
        "robotbattery",
        "Robot vacuum batteries",
        "Replacement rechargeable battery packs for robot vacuum cleaners.",
    ),
    (
        "drill",
        "Cordless drills",
        "Complete powered drills, including bare tools sold without batteries.",
    ),
    (
        "toolbattery",
        "Power tool batteries",
        "Replacement lithium batteries for cordless drills and other power tools.",
    ),
    ("bits", "Drill bits", "Cutting drill bits for wood, metal and masonry. Not powered drills."),
    (
        "toolcase",
        "Tool storage cases",
        "Empty cases and boxes used to store or transport power tools.",
    ),
]

PRODUCTS = [
    (
        "northline",
        "NL-101",
        "earbuds",
        "Auralink Pro ANC earbuds + USB-C case",
        "Complete pair of wireless noise-cancelling earbuds with an electronic charging case.",
        "Audio / Mobile accessories",
        "Auralink",
    ),
    (
        "northline",
        "NL-102",
        "chargecase",
        "Auralink Pro replacement power case",
        "Electronic charging enclosure with internal battery. For lost charging cases. No earbuds supplied.",
        "Audio / Mobile accessories",
        "Auralink",
    ),
    (
        "northline",
        "NL-103",
        "cover",
        "Soft shell for Auralink Pro case — sage",
        "Silicone protective cover with carabiner. Contains no electronics, charging case or earbuds.",
        "Audio / Mobile accessories",
        "Form",
    ),
    (
        "northline",
        "NL-104",
        "tips",
        "Auralink compatible comfort set, S/M/L",
        "Six replacement silicone ear tips for in-ear headphones. Earbuds are not included.",
        "Audio / Mobile accessories",
        "Form",
    ),
    (
        "northline",
        "NL-105",
        "dock",
        "WorkPort 11-in-1 Type-C station",
        "Laptop docking station with dual HDMI, Ethernet, USB ports and 100W pass-through charging. Not a wall charger.",
        "Cables & adapters",
        "WorkPort",
    ),
    (
        "northline",
        "NL-106",
        "charger",
        "65W GaN Type-C travel brick",
        "Compact USB-C wall power adapter for charging laptops and phones. No data, display or docking ports.",
        "Cables & adapters",
        "WorkPort",
    ),
    (
        "homestead",
        "HS-201",
        "grinder",
        "Morning Ritual burr mill",
        "Electric coffee bean grinder with 32 grind settings. Grinds beans only; does not brew coffee.",
        "Kitchen / Coffee",
        "Ritual",
    ),
    (
        "homestead",
        "HS-202",
        "espresso",
        "Morning Ritual Barista 15-bar",
        "Countertop espresso brewing machine with steam wand and portafilter. No integrated grinder.",
        "Kitchen / Coffee",
        "Ritual",
    ),
    (
        "homestead",
        "HS-203",
        "descaler",
        "Barista care, 500 ml",
        "Liquid descaling solution that removes limescale from espresso machines and coffee makers. Not an appliance.",
        "Kitchen / Coffee",
        "Ritual",
    ),
    (
        "homestead",
        "HS-204",
        "vacuum",
        "Orbit R5 automatic floor cleaner",
        "Complete robot vacuum cleaner with navigation, suction motor and charging dock.",
        "Floor care / Orbit",
        "Orbit",
    ),
    (
        "homestead",
        "HS-205",
        "filter",
        "Orbit R5 dust cartridge, twin pack",
        "Two replacement HEPA filters compatible with Orbit robot vacuum cleaners. Vacuum not included.",
        "Floor care / Orbit",
        "Orbit",
    ),
    (
        "homestead",
        "HS-206",
        "robotbattery",
        "Orbit R5 replacement energy pack",
        "Rechargeable 14.4V lithium battery for the Orbit robot vacuum. Replacement battery only.",
        "Floor care / Orbit",
        "Orbit",
    ),
    (
        "ironworks",
        "IW-301",
        "drill",
        "Forge D18 brushless — body only",
        "Complete cordless drill driver motor and chuck. Bare tool: battery and charger sold separately.",
        "Workshop / D18 system",
        "Forge",
    ),
    (
        "ironworks",
        "IW-302",
        "toolbattery",
        "Forge D18 5Ah power pack",
        "18V lithium battery compatible with Forge cordless drills. No drill or charger included.",
        "Workshop / D18 system",
        "Forge",
    ),
    (
        "ironworks",
        "IW-303",
        "bits",
        "Forge masonry set, 6 pieces",
        "Six carbide-tipped drill bits for drilling concrete and brick. Requires a separate powered drill.",
        "Workshop / D18 system",
        "Forge",
    ),
    (
        "ironworks",
        "IW-304",
        "toolcase",
        "D18 carry shell",
        "Empty rigid storage case with foam insert for a cordless drill and batteries. No tools included.",
        "Workshop / D18 system",
        "Forge",
    ),
    (
        "ironworks",
        "IW-305",
        "unmatched",
        "Premium compatible accessory, assorted",
        "Replacement accessory. Supplier has not specified the item, compatible equipment, material or function.",
        "Workshop / Other",
        "Unspecified",
    ),
    (
        "ironworks",
        "IW-306",
        "unmatched",
        "Industrial lubricant, 1 litre",
        "General-purpose lubricating oil for metal workshop machinery. Not a cleaner for coffee appliances.",
        "Workshop / Consumables",
        "Forge",
    ),
]


def demo_catalog():
    suppliers = [
        {
            "id": "northline",
            "name": "Northline Supply",
            "region": "Consumer electronics · NL",
            "products": [],
        },
        {
            "id": "homestead",
            "name": "Homestead Trading",
            "region": "Home & living · UK",
            "products": [],
        },
        {
            "id": "ironworks",
            "name": "Ironworks Direct",
            "region": "Tools & workshop · AU",
            "products": [],
        },
    ]
    for supplier, sku, _, title, description, source_category, brand in PRODUCTS:
        next(s for s in suppliers if s["id"] == supplier)["products"].append(
            {
                "id": sku,
                "title": title,
                "description": description,
                "source_category": source_category,
                "brand": brand,
            }
        )
    harbor, bazaar, mercury = [], {}, []
    broad = {
        "earbuds": (
            "audio-devices",
            "Electronics / Personal audio",
            "Complete headphones and wireless earbuds.",
        ),
        "chargecase": (
            "audio-parts",
            "Electronics / Audio accessories",
            "Earbud charging cases, protective covers, ear tips and cushions. No complete headphones.",
        ),
        "cover": (
            "audio-parts",
            "Electronics / Audio accessories",
            "Earbud charging cases, protective covers, ear tips and cushions. No complete headphones.",
        ),
        "tips": (
            "audio-parts",
            "Electronics / Audio accessories",
            "Earbud charging cases, protective covers, ear tips and cushions. No complete headphones.",
        ),
        "dock": (
            "connectivity",
            "Computing / Hubs & docking",
            "Laptop docking stations and USB data hubs with display and peripheral connections.",
        ),
        "charger": ("power", "Computing / Chargers", "Wall power adapters and USB-C chargers."),
        "grinder": (
            "coffee",
            "Home / Coffee appliances",
            "Coffee bean grinders and espresso brewing machines. No cleaning consumables.",
        ),
        "espresso": (
            "coffee",
            "Home / Coffee appliances",
            "Coffee bean grinders and espresso brewing machines. No cleaning consumables.",
        ),
        "descaler": (
            "coffee-care",
            "Home / Coffee appliance care",
            "Cleaning tablets and descaling liquids for coffee machines.",
        ),
        "vacuum": (
            "floorcare",
            "Home / Vacuum cleaners",
            "Complete vacuum cleaning appliances including robot vacuums.",
        ),
        "filter": (
            "vacuum-parts",
            "Home / Vacuum spare parts",
            "Vacuum cleaner replacement filters and battery packs. No complete vacuum cleaners.",
        ),
        "robotbattery": (
            "vacuum-parts",
            "Home / Vacuum spare parts",
            "Vacuum cleaner replacement filters and battery packs. No complete vacuum cleaners.",
        ),
        "drill": (
            "power-tools",
            "DIY / Power tools",
            "Complete powered tools including bare cordless drills without batteries.",
        ),
        "toolbattery": (
            "tool-power",
            "DIY / Batteries & chargers",
            "Replacement batteries and chargers for cordless power tools.",
        ),
        "bits": (
            "tool-extras",
            "DIY / Tool accessories",
            "Drill bits and empty tool carrying cases. No powered drills or batteries.",
        ),
        "toolcase": (
            "tool-extras",
            "DIY / Tool accessories",
            "Drill bits and empty tool carrying cases. No powered drills or batteries.",
        ),
    }
    for i, (key, label, description) in enumerate(CONCEPTS):
        department = "Electronics" if i < 6 else "Home" if i < 12 else "Workshop"
        harbor.append(
            {"id": f"H-{i + 101}", "path": f"{department} / {label}", "description": description}
        )
        bid, path, desc = broad[key]
        bazaar[bid] = {"id": bid, "path": path, "description": desc}
        prefix = (
            "Replacement parts"
            if key in {"chargecase", "tips", "filter", "robotbattery", "toolbattery"}
            else "Equipment & accessories"
        )
        mercury.append(
            {"id": f"M-{i + 501}", "path": f"{prefix} / {label}", "description": description}
        )
    markets = [
        {
            "id": "harbor",
            "name": "Harbor Market",
            "region": "US · detailed taxonomy",
            "version": "2026.1",
            "categories": harbor,
        },
        {
            "id": "bazaar",
            "name": "Bazaar Collective",
            "region": "UK · broad taxonomy",
            "version": "2026.1",
            "categories": list(bazaar.values()),
        },
        {
            "id": "mercury",
            "name": "Mercury Commerce",
            "region": "AU · parts-first taxonomy",
            "version": "2026.1",
            "categories": mercury,
        },
    ]
    expected = {}
    for _, sku, concept, *_ in PRODUCTS:
        index = next((i for i, c in enumerate(CONCEPTS) if c[0] == concept), None)
        expected[sku] = {
            "harbor": f"H-{index + 101}" if index is not None else "unmatched",
            "bazaar": broad[concept][0] if concept != "unmatched" else "unmatched",
            "mercury": f"M-{index + 501}" if index is not None else "unmatched",
        }
    return suppliers, markets, expected
