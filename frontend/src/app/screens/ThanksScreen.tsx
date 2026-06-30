import { CheckCircle2 } from "lucide-react";

import { ScreenContainer } from "../components/ScreenContainer";

export function ThanksScreen() {
  return (
    <ScreenContainer maxWidth="md">
      <CheckCircle2 className="text-primary" size={88} strokeWidth={1.7} />

      <div className="flex flex-col items-center gap-2 text-center">
        <h1
          className="text-foreground"
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: "7rem",
            fontWeight: 800,
            lineHeight: 1,
          }}
        >
          Bedankt!
        </h1>
        <p
          className="tracking-wide text-muted-foreground"
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: "2.5rem",
            fontWeight: 600,
          }}
        >
          Veel plezier!
        </p>
      </div>

      <p className="text-lg text-muted-foreground">De automaat keert vanzelf terug</p>
    </ScreenContainer>
  );
}
