import { Coins } from "lucide-react";

import { AmountButton, SecondaryButton } from "../components/Buttons";
import { ScreenContainer } from "../components/ScreenContainer";
import { ScreenHeader } from "../components/ScreenHeader";

type WelcomeScreenProps = {
  connected: boolean;
  inventory: number | null;
  presetAmounts: number[];
  statusMessage: string;
  onSelectAmount: (amount: number) => void;
  onCustomAmount: () => void;
};

export function WelcomeScreen({
  connected,
  inventory,
  presetAmounts,
  statusMessage,
  onSelectAmount,
  onCustomAmount,
}: WelcomeScreenProps) {
  return (
    <ScreenContainer maxWidth="lg" status={statusMessage}>
      <ScreenHeader
        icon={<Coins className="text-primary" size={58} strokeWidth={1.5} />}
        title="Consumptiemunten"
        subtitle="Kies het aantal munten"
      />

      <div className="w-full flex flex-col gap-5">
        <div className="grid grid-cols-2 gap-5">
          {presetAmounts.map((amount) => (
            <AmountButton
              key={amount}
              onClick={() => onSelectAmount(amount)}
              disabled={!connected}
            >
              {amount}
            </AmountButton>
          ))}
        </div>

        <SecondaryButton
          onClick={onCustomAmount}
          disabled={!connected}
          className="w-full py-9"
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: "3rem",
            fontWeight: 800,
            lineHeight: 1,
          }}
        >
          Ander aantal
        </SecondaryButton>
      </div>

      {inventory !== null && (
        <p className="text-sm tracking-wide text-muted-foreground">Voorraad: {inventory}</p>
      )}
    </ScreenContainer>
  );
}
