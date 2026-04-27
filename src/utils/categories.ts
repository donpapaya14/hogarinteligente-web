export const CATEGORIES = {
  'cocina': { name: 'Cocina', slug: 'cocina', description: 'Gadgets y utensilios de cocina' },
  'hogar': { name: 'Hogar', slug: 'hogar', description: 'Productos inteligentes para tu casa' },
  'organizacion': { name: 'Organizacion', slug: 'organizacion', description: 'Orden y almacenamiento' },
  'limpieza': { name: 'Limpieza', slug: 'limpieza', description: 'Robots y productos de limpieza' },
  'tecnologia': { name: 'Tecnologia', slug: 'tecnologia', description: 'Tech para el hogar' },
} as const;

export type Category = keyof typeof CATEGORIES;

export function getCategoryName(cat: Category): string {
  return CATEGORIES[cat].name;
}

export function getCategoryBadgeClass(cat: Category): string {
  return `badge badge--${cat}`;
}
