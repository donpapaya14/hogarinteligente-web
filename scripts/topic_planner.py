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
