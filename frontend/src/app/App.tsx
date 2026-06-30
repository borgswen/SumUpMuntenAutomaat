import { useEffect, useMemo, useRef, useState } from "react";
import { Coins } from "lucide-react";

type Screen = "welcome" | "confirm" | "pay" | "dispensing" | "thanks" | "error";

type BackendState =
  | "idle"
  | "selected"
  | "awaiting_payment"
  | "payment_authorized"
  | "dispensing"
  | "complete"
  | "error";

type MachineContext = {
  amount: number;
  price: number;
  transaction_id?: string | null;
  error?: string | null;
  inventory?: number | null;
  dispensed?: number;
};

type BackendEvent =
  | { type: "MachineStateChanged"; payload: { state: BackendState; context: MachineContext } }
  | { type: "PaymentStarted"; payload: { amount?: number; price?: number; transaction_id?: string } }
  | { type: "PaymentSucceeded"; payload: { transaction_id: string } }
  | { type: "PaymentFailed"; payload: { message: string } }
  | { type: "PaymentCancelled"; payload: { transaction_id?: string | null } }
  | { type: "DispensingStarted"; payload: { amount: number } }
  | { type: "DispensingProgress"; payload: { current: number; total: number; inventory: number } }
  | { type: "DispensingFinished"; payload: { amount: number; inventory?: number | null } }
  | { type: "InventoryChanged"; payload: { inventory?: number | null; capacity?: number | null } }
  | { type: "HopperEmpty"; payload: { message?: string; inventory?: number } }
  | { type: "MachineReset"; payload: { reason: string } }
  | { type: "ErrorOccurred"; payload: { message: string } };

type CommandType =
  | "SelectAmount"
  | "ConfirmSelection"
  | "StartPayment"
  | "CancelPayment"
  | "ResetMachine";

const PRESET_AMOUNTS = [5, 10, 20, 50];
const WS_URL = "ws://localhost:8000/ws";

const initialContext: MachineContext = {
  amount: 0,
  price: 0,
  transaction_id: null,
  error: null,
  inventory: null,
  dispensed: 0,
};

function screenForState(state: BackendState): Screen {
  if (state === "selected") return "confirm";
  if (state === "awaiting_payment") return "pay";
  if (state === "payment_authorized" || state === "dispensing") return "dispensing";
  if (state === "complete") return "thanks";
  if (state === "error") return "error";
  return "welcome";
}

function formatPrice(value: number): string {
  return `€${value.toFixed(2).replace(".", ",")}`;
}

export default function App() {
  const [connected, setConnected] = useState(false);
  const [serverState, setServerState] = useState<BackendState>("idle");
  const [context, setContext] = useState<MachineContext>(initialContext);
  const [statusMessage, setStatusMessage] = useState("Verbinding maken...");
  const [inventory, setInventory] = useState<number | null>(null);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const socketRef = useRef<WebSocket | null>(null);

  const screen = useMemo(() => screenForState(serverState), [serverState]);
  const amount = context.amount;
  const total = progress.total || amount;
  const current = serverState === "complete" ? amount : progress.current;
  const progressPercent = total > 0 ? Math.round((current / total) * 100) : 0;

  useEffect(() => {
    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.addEventListener("open", () => {
      setConnected(true);
      setStatusMessage("Verbonden met backend");
    });

    socket.addEventListener("message", (event) => {
      try {
        const message = JSON.parse(event.data) as BackendEvent;
        handleBackendEvent(message);
      } catch (error) {
        console.error("Ongeldig backend-bericht:", error);
      }
    });

    socket.addEventListener("close", () => {
      setConnected(false);
      setStatusMessage("Verbinding verbroken");
    });

    socket.addEventListener("error", () => {
      setConnected(false);
      setStatusMessage("Kan geen verbinding maken met backend");
    });

    return () => socket.close();
  }, []);

  function handleBackendEvent(message: BackendEvent) {
    switch (message.type) {
      case "MachineStateChanged":
        setServerState(message.payload.state);
        setContext({ ...initialContext, ...message.payload.context });
        if (message.payload.state === "idle" || message.payload.state === "selected") {
          setProgress({ current: 0, total: 0 });
        }
        if (typeof message.payload.context.inventory === "number") {
          setInventory(message.payload.context.inventory);
        }
        if (message.payload.context.error) {
          setStatusMessage(message.payload.context.error);
        }
        break;
      case "PaymentStarted":
        setStatusMessage("Betaling gestart");
        break;
      case "PaymentSucceeded":
        setStatusMessage("Betaling ontvangen");
        break;
      case "PaymentFailed":
        setStatusMessage(message.payload.message);
        break;
      case "PaymentCancelled":
        setStatusMessage("Betaling geannuleerd");
        break;
      case "DispensingStarted":
        setProgress({ current: 0, total: message.payload.amount });
        setStatusMessage("Munten worden uitgegeven");
        break;
      case "DispensingProgress":
        setProgress({
          current: message.payload.current,
          total: message.payload.total,
        });
        setInventory(message.payload.inventory);
        break;
      case "DispensingFinished":
        setProgress({
          current: message.payload.amount,
          total: message.payload.amount,
        });
        if (typeof message.payload.inventory === "number") {
          setInventory(message.payload.inventory);
        }
        setStatusMessage("Dispensatie voltooid");
        break;
      case "InventoryChanged":
        if (typeof message.payload.inventory === "number") {
          setInventory(message.payload.inventory);
        }
        break;
      case "HopperEmpty":
        setInventory(0);
        setStatusMessage(message.payload.message || "Hopper leeg");
        break;
      case "MachineReset":
        setStatusMessage(
          message.payload.reason === "completed"
            ? "Klaar voor de volgende bestelling"
            : "Machine gereset"
        );
        break;
      case "ErrorOccurred":
        setStatusMessage(message.payload.message);
        break;
      default:
        break;
    }
  }

  function sendCommand(type: CommandType, payload?: Record<string, unknown>) {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      setStatusMessage("Backend niet beschikbaar");
      return;
    }
    socketRef.current.send(JSON.stringify({ type, payload: payload || {} }));
  }

  return (
    <div
      className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center select-none overflow-hidden"
      style={{ fontFamily: "var(--font-sans)" }}
    >
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
                onClick={() => sendCommand("SelectAmount", { amount: n })}
                disabled={!connected}
                className="bg-primary text-primary-foreground rounded-2xl py-10 hover:brightness-110 active:scale-95 transition-all duration-150 shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
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

          <p className="text-muted-foreground text-lg min-h-7">{statusMessage}</p>
          {inventory !== null && (
            <p className="text-muted-foreground text-sm">Voorraad: {inventory}</p>
          )}
        </div>
      )}

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
              {formatPrice(context.price)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 w-full">
            <button
              onClick={() => sendCommand("ResetMachine")}
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
              onClick={() => sendCommand("ConfirmSelection")}
              className="bg-primary text-primary-foreground rounded-2xl py-6 hover:brightness-110 active:scale-95 transition-all duration-150"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.5rem",
                fontWeight: 800,
                boxShadow: "0 8px 32px rgba(245,166,35,0.25)",
              }}
            >
              Bevestigen →
            </button>
          </div>
        </div>
      )}

      {screen === "pay" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-12">
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
              Klaar voor betaling
            </h1>
            <p className="text-muted-foreground text-xl tracking-wide">
              {amount} munten voor {formatPrice(context.price)}
            </p>
          </div>

          <button
            onClick={() => sendCommand("StartPayment")}
            className="bg-primary text-primary-foreground rounded-2xl px-14 py-7 hover:brightness-110 active:scale-95 transition-all duration-150"
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "1.75rem",
              fontWeight: 800,
              boxShadow: "0 8px 32px rgba(245,166,35,0.25)",
            }}
          >
            Start betaling
          </button>

          <button
            onClick={() => sendCommand("CancelPayment")}
            className="text-muted-foreground hover:text-foreground transition-colors text-lg"
          >
            Annuleren
          </button>
          <p className="text-muted-foreground text-lg min-h-7">{statusMessage}</p>
        </div>
      )}

      {screen === "dispensing" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-10">
          <div className="flex flex-col items-center gap-2">
            <span className="text-accent text-5xl">✓</span>
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
                  width: `${progressPercent}%`,
                  boxShadow: "0 0 20px rgba(245,166,35,0.6)",
                }}
              />
            </div>
            <div
              className="flex justify-between text-muted-foreground"
              style={{ fontFamily: "var(--font-mono)", fontSize: "1.1rem" }}
            >
              <span>
                {current} / {total}
              </span>
              <span>{progressPercent}%</span>
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
            {current}
          </span>
        </div>
      )}

      {screen === "thanks" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-10">
          <div className="text-primary" style={{ fontSize: "6rem", lineHeight: 1 }}>
            ✓
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

          <p className="text-muted-foreground text-lg">
            De automaat keert vanzelf terug
          </p>
        </div>
      )}

      {screen === "error" && (
        <div className="w-full max-w-xl px-10 flex flex-col items-center gap-8 text-center">
          <h1
            className="text-destructive"
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "3.5rem",
              fontWeight: 800,
            }}
          >
            Er ging iets mis
          </h1>
          <p className="text-muted-foreground text-xl">{statusMessage}</p>
          <p className="text-muted-foreground text-lg">
            De automaat herstelt automatisch
          </p>
          <button
            onClick={() => sendCommand("ResetMachine")}
            className="border-2 border-border text-foreground rounded-2xl px-10 py-5 hover:border-primary/40 transition-all duration-150"
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "1.25rem",
              fontWeight: 700,
            }}
          >
            Reset
          </button>
        </div>
      )}
    </div>
  );
}
