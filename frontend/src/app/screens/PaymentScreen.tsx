import { LoaderCircle } from "lucide-react";

import { PrimaryButton, SecondaryButton } from "../components/Buttons";
import { ScreenContainer } from "../components/ScreenContainer";
import { formatPrice } from "../utils/format";

type PaymentScreenProps = {
  amount: number;
  price: number;
  paymentStarted: boolean;
  statusMessage: string;
  onStartPayment: () => void;
  onCancel: () => void;
};

export function PaymentScreen({
  amount,
  price,
  paymentStarted,
  statusMessage,
  onStartPayment,
  onCancel,
}: PaymentScreenProps) {
  return (
    <ScreenContainer maxWidth="md" status={statusMessage}>
      <div className="flex flex-col items-center gap-3 text-center">
        <h1
          className="text-foreground"
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: "3.5rem",
            fontWeight: 800,
            lineHeight: 1.15,
          }}
        >
          {paymentStarted ? "Volg de instructies" : "Klaar voor betaling"}
        </h1>
        <p className="text-xl tracking-wide text-muted-foreground">
          {amount} munten voor {formatPrice(price)}
        </p>
      </div>

      {paymentStarted ? (
        <div className="flex flex-col items-center gap-5">
          <LoaderCircle className="animate-spin text-primary" size={82} strokeWidth={1.8} />
          <p className="text-xl tracking-widest text-muted-foreground">Even geduld...</p>
        </div>
      ) : (
        <PrimaryButton onClick={onStartPayment} className="px-14 py-7">
          Start betaling
        </PrimaryButton>
      )}

      <SecondaryButton onClick={onCancel} className="px-10 py-4">
        Annuleren
      </SecondaryButton>
    </ScreenContainer>
  );
}
