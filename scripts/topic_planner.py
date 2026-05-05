"""
Plans topics avoiding duplicates and rotating categories.
Reads existing articles in src/content/blog/ to avoid repetition.
"""

import random
import re
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent / "src" / "content" / "blog"

CATEGORIES = ["kitchen", "smart-home", "organization", "cleaning", "energy-saving"]

ARTICLE_FORMULAS = {
    "kitchen": [
        "Kitchen gadget on Amazon with real name, price, what it does and whether it's worth it",
        "Comparison of 3 kitchen tools on Amazon with pros, cons and which to choose",
        "Small appliance that saves time in the kitchen: name, price, how it works",
        "Best accessories for [specific kitchen task] with Amazon links and real analysis",
        "Kitchen organization system that saves 20 minutes a day with numbered steps",
        "One cooking mistake that reduces appliance lifespan with fix and money saved",
    ],
    "smart-home": [
        "Smart home product: what it does, how it works, price on Amazon and real experience",
        "Comparison of smart plugs/bulbs/cameras with real names and Amazon prices",
        "Gadget that transforms your home for under $30: name, function, Amazon link",
        "Alexa vs Google Home: real comparison for automating your home with current prices",
        "Smart thermostat guide: how much it saves and which one is worth buying",
    ],
    "organization": [
        "Organization system for [home area] with Amazon products and before/after results",
        "Best Amazon organizers for kitchen/bathroom/closet with prices and links",
        "Minimalist organization method applied with specific Amazon products",
        "Pantry organization guide that reduces food waste with step-by-step system",
        "Home filing system that saves time: specific method with materials needed",
    ],
    "cleaning": [
        "Robot vacuum comparison: best cheap models on Amazon with real performance data",
        "Cleaning products that actually work: real names, prices and where to buy",
        "Cleaning gadget you didn't know existed: name, Amazon price, how it works",
        "Natural cleaning solutions using household ingredients: specific chemistry explained",
        "One dangerous chemical combination in cleaning products: specific compounds and risk",
    ],
    "energy-saving": [
        "Home hack that cuts electricity bill by specific percentage: average annual saving",
        "Temperature setting that saves most energy: specific degrees and monthly saving",
        "Appliance you're using wrong that increases electricity bill: specific mistake and fix",
        "Solar panel basics: what it costs, what it saves and realistic payback period",
        "Humidity control without a dehumidifier: specific physics and materials needed",
    ],
}


def get_existing_titles() -> set[str]:
    titles = set()
    if not BLOG_DIR.exists():
        return titles
    for md_file in BLOG_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        if match:
            titles.add(match.group(1).lower().strip())
    return titles


def get_category_counts() -> dict[str, int]:
    counts = {cat: 0 for cat in CATEGORIES}
    if not BLOG_DIR.exists():
        return counts
    for md_file in BLOG_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        match = re.search(r'^category:\s*["\']?([^"\'\n]+)["\']?\s*$', content, re.MULTILINE)
        if match and match.group(1).strip() in counts:
            counts[match.group(1).strip()] += 1
    return counts


def pick_category() -> str:
    counts = get_category_counts()
    min_count = min(counts.values())
    least_covered = [cat for cat, count in counts.items() if count == min_count]
    return random.choice(least_covered)


def pick_formula(category: str) -> str:
    formulas = ARTICLE_FORMULAS.get(category, list(ARTICLE_FORMULAS.values())[0])
    return random.choice(formulas)


def plan_topic() -> dict:
    category = pick_category()
    formula = pick_formula(category)
    existing = get_existing_titles()
    return {
        "category": category,
        "formula": formula,
        "existing_titles": list(existing)[:20],
        "existing_count": len(existing),
    }
