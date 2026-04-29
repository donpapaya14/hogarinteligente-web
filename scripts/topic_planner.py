"""
Planifica temas evitando duplicados y rotando categorías.
Lee artículos existentes en src/content/blog/ para evitar repetir.
"""

import os
import random
import re
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent / "src" / "content" / "blog"

CATEGORIES = ["cocina", "hogar", "organizacion", "limpieza", "tecnologia"]

ARTICLE_FORMULAS = {
    "cocina": [
        "Gadget de cocina de Amazon con nombre real, precio, para qué sirve y por qué merece la pena comprarlo",
        "Comparativa de 3 utensilios de cocina de Amazon con pros, contras y cuál elegir según uso",
        "Electrodoméstico pequeño que ahorra tiempo en la cocina: nombre, precio, cómo funciona",
        "Los 5 mejores accesorios para [tarea de cocina] con enlaces a Amazon y análisis real",
    ],
    "hogar": [
        "Producto inteligente para el hogar: qué hace, cómo funciona, precio en Amazon y experiencia real",
        "Comparativa de enchufes/bombillas/cámaras inteligentes con nombres reales y precios Amazon",
        "Gadget que transforma tu hogar por menos de 30 euros: nombre, función, enlace Amazon",
    ],
    "organizacion": [
        "Sistema de organización para [zona de la casa] con productos de Amazon y fotos de antes/después",
        "Los mejores organizadores de Amazon para cocina/baño/armario con precios y enlaces",
        "Método de organización KonMari/minimalista aplicado con productos concretos de Amazon",
    ],
    "limpieza": [
        "Robot aspirador: comparativa de modelos baratos en Amazon con rendimiento real",
        "Productos de limpieza que funcionan de verdad: nombres reales, precios y dónde comprar",
        "Gadget de limpieza que no sabías que existía: nombre, precio Amazon, cómo funciona",
    ],
    "tecnologia": [
        "Gadget tech para el hogar por menos de X euros: nombre, qué hace, enlace Amazon",
        "Alexa vs Google Home: comparativa real para automatizar tu casa con precios actuales",
        "Los 5 gadgets más útiles de Amazon para tu hogar con enlaces directos",
    ],
}


def get_existing_titles() -> set[str]:
    """Lee títulos de artículos existentes del frontmatter."""
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
    """Cuenta artículos por categoría."""
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
    """Elige categoría con menos artículos."""
    counts = get_category_counts()
    min_count = min(counts.values())
    least_covered = [cat for cat, count in counts.items() if count == min_count]
    return random.choice(least_covered)


def pick_formula(category: str) -> str:
    """Elige fórmula aleatoria para la categoría."""
    formulas = ARTICLE_FORMULAS.get(category, list(ARTICLE_FORMULAS.values())[0])
    return random.choice(formulas)


def plan_topic() -> dict:
    """Devuelve categoría y fórmula para el próximo artículo."""
    category = pick_category()
    formula = pick_formula(category)
    existing = get_existing_titles()
    return {
        "category": category,
        "formula": formula,
        "existing_titles": list(existing)[:20],
        "existing_count": len(existing),
    }
