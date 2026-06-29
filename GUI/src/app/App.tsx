import { useState, useEffect } from "react";
import { Coins } from "lucide-react";

type Screen = "welcome" | "confirm" | "custom" | "pay" | "dispensing" | "thanks";

const PRICE_PER_COIN = 1.55;
const PRESET_AMOUNTS = [5, 10, 20, 50];

function formatPrice(amount: number): string {
  return `€${(amount * PRICE_PER_COIN).toFixed(2).replace(".", ",")}`;
}

export default function App() {
  const [screen, setScreen] = useState<Screen>("welcome");
  const [amount, setAmount] = useState(0);
  const [customInput, setCustomInput] = useState("");
  const [dispensed, setDispensed] = useState(0);
  const [countdown, setCountdown] = useState(5);

  // Dispensing animation — fixed 3.5s window
  useEffect(() => {
    if (screen !== "dispensing") return;
    setDispensed(0);
    const duration = 3500;
    const start = Date.now();
    const interval = setInterval(() => {
      const progress = Math.min((Date.now() - start) / duration, 1);
      setDispensed(Math.floor(progress * amount));
      if (progress >= 1) {
        clearInterval(interval);
        setTimeout(() => setScreen("thanks"), 600);
      }
    }, 40);
    return () => clearInterval(interval);
  }, [screen, amount]);

  // Countdown on thanks screen
  useEffect(() => {
    if (screen !== "thanks") return;
    setCountdown(5);
    const interval = setInterval(() => {
      setCountdown((prev) => Math.max(prev - 1, 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [screen]);

  useEffect(() => {
    if (screen === "thanks" && countdown === 0) {
      setTimeout(() => {
        setScreen("welcome");
        setAmount(0);
        setCustomInput("");
      }, 300);
    }
  }, [countdown, screen]);

  const selectAmount = (n: number) => {
    setAmount(n);
    setScreen("confirm");
  };

  const handleNumpad = (key: string) => {
    if (key === "C") {
      setCustomInput("");
    } else if (key === "←") {
      setCustomInput((prev) => prev.slice(0, -1));
    } else {
      setCustomInput((prev) => {
        const next = prev + key;
        if (parseInt(next) > 9999) return prev;
        return next;
      });
    }
  };

  const customAmount = customInput ? parseInt(customInput) : 0;

  const startPayment = () => {
    setScreen("pay");
    setTimeout(() => {
      setDispensed(0);
      setScreen("dispensing");
    }, 3000);
  };

  return (
    <div
      className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center select-none overflow-hidden"
      style={{ fontFamily: "var(--font-sans)" }}
    >
      {/* ── WELKOM / KIES AANTAL ───────────────────────────────────── */}
      {screen === "welcome" && (
        <div className="w-full max-w-2xl px-10 flex flex-col items-center gap-12">
          <div className="flex flex-col items-center gap-4">
            <Coins className="text-primary" size={56} strokeWidth={1.5} />
            <h1
              className="text-5xl font-extrabold tracking-widest text-foreground text-center uppercase"
              style={{ fontFamily: "var(--font-heading)" }}
            >
              Consumptiemunten
            </h1>
            <p className="text-muted-foreground text-xl tracking-wider">
              Kies het aantal munten
            </p>
          </div>

          <div className="grid grid-cols-2 gap-5 w-full">
            {PRESET_AMOUNTS.map((n) => (
              <button
                key={n}
                onClick={() => selectAmount(n)}
                className="bg-primary text-primary-foreground rounded-2xl py-10 hover:brightness-110 active:scale-95 transition-all duration-150 shadow-lg"
                style={{
                  fontFamily: "var(--font-heading)",
                  fontSize: "5rem",
                  fontWeight: 800,
                  lineHeight: 1,
                  boxShadow: "0 8px 32px rgba(245,166,35,0.25)",
                }}
              >
                {n}
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              setCustomInput("");
              setScreen("custom");
            }}
            className="w-full border-2 border-border text-foreground rounded-2xl py-6 hover:border-primary/50 hover:text-primary transition-all duration-150"
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "1.5rem",
              fontWeight: 700,
              letterSpacing: "0.05em",
            }}
          >
            Ander aantal
          </button>
        </div>
      )}

      {/* ── BEVESTIGEN ─────────────────────────────────────────────── */}
      {screen === "confirm" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-10">
          <p
            className="text-muted-foreground tracking-widest uppercase text-lg"
            style={{ fontFamily: "var(--font-heading)", fontWeight: 700 }}
          >
            Controleer bestelling
          </p>

          <div className="bg-card rounded-3xl w-full px-10 py-10 flex flex-col items-center gap-5 border border-border">
            <span
              className="text-foreground leading-none"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "9rem",
                fontWeight: 800,
              }}
            >
              {amount}
            </span>
            <span className="text-muted-foreground text-xl tracking-wide">
              munten
            </span>
            <div className="w-full h-px bg-border" />
            <span
              className="text-primary leading-none"
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "3.5rem",
                fontWeight: 700,
              }}
            >
              {formatPrice(amount)}
            </span>
            <span className="text-muted-foreground text-base">
              Iedere munt kost €1,55
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 w-full">
            <button
              onClick={() => setScreen("welcome")}
              className="border-2 border-border text-foreground rounded-2xl py-6 hover:border-primary/40 transition-all duration-150"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.5rem",
                fontWeight: 700,
              }}
            >
              ← Terug
            </button>
            <button
              onClick={startPayment}
              className="bg-primary text-primary-foreground rounded-2xl py-6 hover:brightness-110 active:scale-95 transition-all duration-150"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.5rem",
                fontWeight: 800,
                boxShadow: "0 8px 32px rgba(245,166,35,0.25)",
              }}
            >
              Betalen →
            </button>
          </div>
        </div>
      )}

      {/* ── ANDER AANTAL / NUMPAD ──────────────────────────────────── */}
      {screen === "custom" && (
        <div className="w-full max-w-sm px-8 flex flex-col items-center gap-7">
          <p
            className="text-muted-foreground tracking-widest uppercase text-lg"
            style={{ fontFamily: "var(--font-heading)", fontWeight: 700 }}
          >
            Voer aantal in
          </p>

          <div className="bg-card rounded-2xl w-full px-8 py-6 flex flex-col items-center gap-2 border border-border min-h-[7rem] justify-center">
            <span
              className="text-foreground leading-none"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: customInput.length > 3 ? "5rem" : "7rem",
                fontWeight: 800,
                color: customInput ? undefined : "var(--muted-foreground)",
                opacity: customInput ? 1 : 0.3,
              }}
            >
              {customInput || "0"}
            </span>
            {customAmount > 0 && (
              <span
                className="text-primary"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "1.5rem",
                  fontWeight: 700,
                }}
              >
                {formatPrice(customAmount)}
              </span>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3 w-full">
            {["7", "8", "9", "4", "5", "6", "1", "2", "3", "C", "0", "←"].map(
              (key) => (
                <button
                  key={key}
                  onClick={() => handleNumpad(key)}
                  className={`rounded-2xl py-5 transition-all duration-100 active:scale-95 ${
                    key === "C"
                      ? "bg-destructive/20 text-destructive hover:bg-destructive/30"
                      : "bg-secondary text-secondary-foreground hover:brightness-125"
                  }`}
                  style={{
                    fontFamily: "var(--font-heading)",
                    fontSize: "2rem",
                    fontWeight: 700,
                  }}
                >
                  {key}
                </button>
              )
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 w-full">
            <button
              onClick={() => setScreen("welcome")}
              className="border-2 border-border text-foreground rounded-2xl py-5 hover:border-primary/40 transition-all"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.25rem",
                fontWeight: 700,
              }}
            >
              ← Terug
            </button>
            <button
              onClick={() => {
                if (customAmount < 1) return;
                setAmount(customAmount);
                setScreen("confirm");
              }}
              disabled={!customAmount || customAmount < 1}
              className="bg-primary text-primary-foreground rounded-2xl py-5 hover:brightness-110 active:scale-95 transition-all disabled:opacity-25 disabled:cursor-not-allowed"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.25rem",
                fontWeight: 800,
                boxShadow: customAmount > 0
                  ? "0 8px 32px rgba(245,166,35,0.25)"
                  : "none",
              }}
            >
              Volgende →
            </button>
          </div>
        </div>
      )}

      {/* ── BETAALTERMINAL ─────────────────────────────────────────── */}
      {screen === "pay" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-16">
          <div className="flex flex-col items-center gap-3 text-center">
            <h1
              className="text-foreground leading-tight"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "3.5rem",
                fontWeight: 800,
                lineHeight: 1.15,
              }}
            >
              Volg de instructies
              <br />
              op de betaalterminal
            </h1>
          </div>

          <div className="flex flex-col items-center gap-5">
            <div
              className="w-20 h-20 rounded-full border-4 border-primary border-t-transparent"
              style={{ animation: "spin 0.9s linear infinite" }}
            />
            <p className="text-muted-foreground text-xl tracking-widest">
              ⌛ Even geduld...
            </p>
          </div>

          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* ── MUNTEN UITGEVEN ────────────────────────────────────────── */}
      {screen === "dispensing" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-10">
          <div className="flex flex-col items-center gap-2">
            <span className="text-accent text-5xl">✔</span>
            <p
              className="text-muted-foreground tracking-widest uppercase text-lg"
              style={{ fontFamily: "var(--font-heading)", fontWeight: 700 }}
            >
              Betaling ontvangen
            </p>
          </div>

          <h2
            className="text-foreground text-center"
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "2.25rem",
              fontWeight: 700,
            }}
          >
            Munten worden uitgegeven
          </h2>

          <div className="w-full flex flex-col gap-4">
            <div className="w-full bg-secondary rounded-full h-7 overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-75"
                style={{
                  width: `${amount > 0 ? (dispensed / amount) * 100 : 0}%`,
                  boxShadow: "0 0 20px rgba(245,166,35,0.6)",
                }}
              />
            </div>
            <div
              className="flex justify-between text-muted-foreground"
              style={{ fontFamily: "var(--font-mono)", fontSize: "1.1rem" }}
            >
              <span>
                {dispensed} / {amount}
              </span>
              <span>
                {amount > 0 ? Math.round((dispensed / amount) * 100) : 0}%
              </span>
            </div>
          </div>

          <span
            className="text-foreground leading-none"
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "8rem",
              fontWeight: 800,
            }}
          >
            {dispensed}
          </span>
        </div>
      )}

      {/* ── BEDANKT ────────────────────────────────────────────────── */}
      {screen === "thanks" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-10">
          <div
            className="text-primary"
            style={{ fontSize: "6rem", lineHeight: 1 }}
          >
            ✔
          </div>

          <div className="flex flex-col items-center gap-3">
            <h1
              className="text-foreground"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "5rem",
                fontWeight: 800,
                lineHeight: 1,
              }}
            >
              Bedankt!
            </h1>
            <p className="text-muted-foreground text-2xl tracking-wide">
              Veel plezier!
            </p>
          </div>

          <div className="flex flex-col items-center gap-3">
            <p className="text-muted-foreground text-lg">
              Dit scherm sluit over
            </p>
            <div
              className="w-28 h-28 rounded-full border-4 flex items-center justify-center"
              style={{ borderColor: "rgba(245,166,35,0.35)" }}
            >
              <span
                className="text-primary"
                style={{
                  fontFamily: "var(--font-heading)",
                  fontSize: "4rem",
                  fontWeight: 800,
                  lineHeight: 1,
                }}
              >
                {countdown}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
