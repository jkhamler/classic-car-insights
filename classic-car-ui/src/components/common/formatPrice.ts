export function formatPrice(amount: number | null | undefined, currency = 'GBP'): string {
  if (amount === null || amount === undefined) return '—';
  const symbol = currency === 'USD' ? '$' : currency === 'EUR' ? '€' : '£';
  return `${symbol}${amount.toLocaleString('en-GB', { maximumFractionDigits: 0 })}`;
}
