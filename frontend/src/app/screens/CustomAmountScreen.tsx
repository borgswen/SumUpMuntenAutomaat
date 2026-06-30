import { NumpadButton, PrimaryButton, SecondaryButton } from "../components/Buttons";
import { ScreenContainer } from "../components/ScreenContainer";
import { formatPrice, priceForAmount } from "../utils/format";

type CustomAmountScreenProps = {
  value: string;
  pricePerCoin: number;
  onChange: (value: string) => void;
  onSubmit: (amount: number) => void;
  onBack: () => void;
};

const keys = ["7", "8", "9", "4", "5", "6", "1", "2", "3", "C", "0", "←"];

export function CustomAmountScreen({
  value,
  pricePerCoin,
  onChange,
  onSubmit,
  onBack,
}: CustomAmountScreenProps) {
  const amount = value ? parseInt(value, 10) : 0;
  const displayPrice = formatPrice(priceForAmount(amount, pricePerCoin));

  function handleKey(key: string) {
    if (key === "C") {
      onChange("");
      return;
    }
    if (key === "←") {
      onChange(value.slice(0, -1));
      return;
    }
    const next = `${value}${key}`;
    if (parseInt(next, 10) > 9999) return;
    onChange(next);
  }

  return (
    <ScreenContainer maxWidth="sm">
      <p
        className="text-lg uppercase tracking-widest text-muted-foreground"
        style={{ fontFamily: "var(--font-heading)", fontWeight: 700 }}
      >
        Voer aantal in
      </p>

      <div className="flex min-h-32 w-full flex-col items-center justify-center gap-2 rounded-2xl border border-border bg-card px-8 py-6">
        <span
          className="text-foreground"
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: value.length > 3 ? "5rem" : "7rem",
            fontWeight: 800,
            lineHeight: 1,
            opacity: value ? 1 : 0.3,
          }}
        >
          {value || "0"}
        </span>
        {amount > 0 && (
          <span className="text-primary" style={{ fontFamily: "var(--font-mono)", fontSize: "1.5rem", fontWeight: 700 }}>
            {displayPrice}
          </span>
        )}
      </div>

      <div className="grid w-full grid-cols-3 gap-3">
        {keys.map((key) => (
          <NumpadButton key={key} onClick={() => handleKey(key)}>
            {key}
          </NumpadButton>
        ))}
      </div>

      <div className="grid w-full grid-cols-2 gap-4">
        <SecondaryButton onClick={onBack} className="w-full">
          ← Terug
        </SecondaryButton>
        <PrimaryButton
          onClick={() => onSubmit(amount)}
          disabled={amount < 1}
          className="w-full"
        >
          Volgende →
        </PrimaryButton>
      </div>
    </ScreenContainer>
  );
}
