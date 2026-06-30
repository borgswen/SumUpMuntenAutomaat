import { PrimaryButton, SecondaryButton } from "../components/Buttons";
import { ScreenContainer } from "../components/ScreenContainer";
import { formatPrice } from "../utils/format";

type ConfirmScreenProps = {
  amount: number;
  price: number;
  onConfirm: () => void;
  onBack: () => void;
};

export function ConfirmScreen({ amount, price, onConfirm, onBack }: ConfirmScreenProps) {
  return (
    <ScreenContainer maxWidth="md">
      <p
        className="text-lg uppercase tracking-widest text-muted-foreground"
        style={{ fontFamily: "var(--font-heading)", fontWeight: 700 }}
      >
        Controleer bestelling
      </p>

      <div className="flex w-full flex-col items-center gap-5 rounded-3xl border border-border bg-card px-10 py-10">
        <span
          className="text-foreground"
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: "9rem",
            fontWeight: 800,
            lineHeight: 1,
          }}
        >
          {amount}
        </span>
        <span className="text-xl tracking-wide text-muted-foreground">munten</span>
        <div className="h-px w-full bg-border" />
        <span
          className="text-primary"
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "3.5rem",
            fontWeight: 700,
            lineHeight: 1,
          }}
        >
          {formatPrice(price)}
        </span>
      </div>

      <div className="grid w-full grid-cols-2 gap-4">
        <SecondaryButton onClick={onBack} className="w-full">
          ← Terug
        </SecondaryButton>
        <PrimaryButton onClick={onConfirm} className="w-full">
          Bevestigen →
        </PrimaryButton>
      </div>
    </ScreenContainer>
  );
}
