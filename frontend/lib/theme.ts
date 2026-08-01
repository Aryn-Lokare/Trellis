export const COHERE_COLORS = {
  primary: '#17171c',
  cohereBlack: '#000000',
  ink: '#212121',
  deepGreen: '#003c33',
  darkNavy: '#071829',
  canvas: '#ffffff',
  softStone: '#eeece7',
  paleGreen: '#edfce9',
  hairline: '#d9d9dd',
  borderLight: '#e5e7eb',
  muted: '#93939f',
  slate: '#75758a',
  actionBlue: '#1863dc',
  coral: '#ff7759',
  error: '#b30000',
} as const;

export const ENTITY_TYPE_COLORS: Record<string, string> = {
  regulation: '#ff7759',
  vendor: '#1863dc',
  company: '#4c6ee6',
  person: '#9b60aa',
  system: '#003c33',
  policy: '#75758a',
  audio: '#ffad9b',
  schematic: '#071829',
  table: '#edfce9',
  pdf: '#1863dc',
};

export function getEntityTypeColor(type: string): string {
  const normalized = type.toLowerCase().trim();
  return ENTITY_TYPE_COLORS[normalized] || '#75758a';
}
