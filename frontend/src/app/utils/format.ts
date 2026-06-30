export function formatPrice(value: number): string {
  return `€${value.toFixed(2).replace(".", ",")}`;
}

export function priceForAmount(amount: number, pricePerCoin: number): number {
  return Math.round(amount * pricePerCoin * 100) / 100;
}
