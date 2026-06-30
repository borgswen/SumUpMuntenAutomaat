import { CircleX } from "lucide-react";

import { PrimaryButton, SecondaryButton } from "../components/Buttons";
import { ScreenContainer } from "../components/ScreenContainer";

type PaymentFailedScreenProps = {
  message: string;
  onRetry: () => void;
  onBack: () => void;
};

export function PaymentFailedScreen({ message, onRetry, onBack }: PaymentFailedScreenProps) {
  return (
    <ScreenContainer maxWidth="md">
      <CircleX className="text-destructive" size={90} strokeWidth={1.8} />

      <div className="flex flex-col items-center gap-3 text-center">
        <h1
          className="text-foreground"
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: "5rem",
            fontWeight: 800,
            lineHeight: 1,
          }}
        >
          Betaling mislukt
        </h1>
        <p className="text-xl text-muted-foreground">
          {message || "Er is iets misgegaan met de betaling. Probeer het opnieuw of ga terug."}
        </p>
      </div>

      <div className="grid w-full grid-cols-2 gap-4">
        <SecondaryButton onClick={onBack} className="w-full">
          Terug
        </SecondaryButton>
        <PrimaryButton onClick={onRetry} className="w-full">
          Opnieuw proberen
        </PrimaryButton>
      </div>
    </ScreenContainer>
  );
}
