export const formatHoursLabel = (hours: string | number): string => {
  const n = typeof hours === 'number' ? hours : parseFloat(hours);
  if (!Number.isFinite(n)) return '';
  const text = Number.isInteger(n) ? String(n) : String(n);
  return n === 1 ? '1 HR' : `${text} HRS`;
};

const MES_ES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

export const monthNameEs = (isoDate: string): string => {
  const idx = new Date(`${isoDate}T00:00:00`).getMonth();
  const name = MES_ES[idx] ?? '';
  return name ? name.charAt(0).toUpperCase() + name.slice(1) : '';
};
