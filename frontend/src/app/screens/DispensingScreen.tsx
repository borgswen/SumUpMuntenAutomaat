import { CheckCircle2 } from "lucide-react";

import { ProgressBar } from "../components/ProgressBar";
import { ScreenContainer } from "../components/ScreenContainer";

type DispensingScreenProps = {
  current: number;
  total: number;
};

export function DispensingScreen({ current, total }: DispensingScreenProps) {
  return (
    <ScreenContainer maxWidth="md">
      <div className="flex flex-col items-center gap-2">
        <CheckCircle2 className="text-accent" size={58} strokeWidth={1.8} />
        <p
          className="text-lg uppercase tracking-widest text-muted-foreground"
          style={{ fontFamily: "var(--font-heading)", fontWeight: 700 }}
        >
          Betaling ontvangen
        </p>
      </div>

      <h2
        className="text-center text-foreground"
        style={{
          fontFamily: "var(--font-heading)",
          fontSize: "2.25rem",
          fontWeight: 700,
        }}
      >
        Munten worden uitgegeven
      </h2>

      <ProgressBar current={current} total={total} />

      <span
        className="text-foreground"
        style={{
          fontFamily: "var(--font-heading)",
          fontSize: "8rem",
          fontWeight: 800,
          lineHeight: 1,
        }}
      >
        {current}
      </span>
    </ScreenContainer>
  );
}
