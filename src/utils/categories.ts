export const CATEGORIES = {
  'kitchen': { name: 'Kitchen Gadgets', slug: 'kitchen', description: 'Best kitchen gadgets reviewed' },
  'smart-home': { name: 'Smart Home', slug: 'smart-home', description: 'Automate your home' },
  'organization': { name: 'Home Organization', slug: 'organization', description: 'Organize your space' },
  'cleaning': { name: 'Cleaning Tips', slug: 'cleaning', description: 'Clean smarter not harder' },
  'energy-saving': { name: 'Energy Saving', slug: 'energy-saving', description: 'Cut your electricity bill' }
} as const;

export type Category = keyof typeof CATEGORIES;

export function getCategoryName(cat: Category): string {
  return CATEGORIES[cat].name;
}

export function getCategoryBadgeClass(cat: Category): string {
  return `badge badge--${cat}`;
}
