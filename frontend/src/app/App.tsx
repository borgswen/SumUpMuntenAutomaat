import { useMemo, useRef, useState, useEffect } from "react";

import { DEFAULT_PRESET_AMOUNTS, DEFAULT_PRICE_PER_COIN } from "../config/defaults";
import { ConfirmScreen } from "./screens/ConfirmScreen";
import { CustomAmountScreen } from "./screens/CustomAmountScreen";
import { DispensingScreen } from "./screens/DispensingScreen";
import { PaymentFailedScreen } from "./screens/PaymentFailedScreen";
import { PaymentScreen } from "./screens/PaymentScreen";
import { ThanksScreen } from "./screens/ThanksScreen";
import { WelcomeScreen } from "./screens/WelcomeScreen";
import type { BackendEvent, BackendState, CommandType, MachineContext, ProgressState, Screen } from "./types";

const WS_URL = "ws://localhost:8000/ws";

const initialContext: MachineContext = {
  amount: 0,
  price: 0,
  transaction_id: null,
  error: null,
  inventory: null,
  dispensed: 0,
};

type LastOrder = {
  amount: number;
  price: number;
};

function screenForState(state: BackendState): Screen {
  if (state === "selected") return "confirm";
  if (state === "awaiting_payment") return "pay";
  if (state === "payment_authorized" || state === "dispensing") return "dispensing";
  if (state === "complete") return "thanks";
  if (state === "error") return "failed";
  return "welcome";
}

function isCancellationMessage(message: string): boolean {
  const normalized = message.toLowerCase();
  return normalized.includes("cancel") || normalized.includes("annuleer");
}

export default function App() {
  const [connected, setConnected] = useState(false);
  const [serverState, setServerState] = useState<BackendState>("idle");
  const [context, setContext] = useState<MachineContext>(initialContext);
  const [statusMessage, setStatusMessage] = useState("Verbinding maken...");
  const [inventory, setInventory] = useState<number | null>(null);
  const [progress, setProgress] = useState<ProgressState>({ current: 0, total: 0 });
  const [customInput, setCustomInput] = useState("");
  const [showCustomAmount, setShowCustomAmount] = useState(false);
  const [paymentStarted, setPaymentStarted] = useState(false);
  const [paymentFailed, setPaymentFailed] = useState(false);
  const [failureMessage, setFailureMessage] = useState("");
  const [lastOrder, setLastOrder] = useState<LastOrder | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const screen = useMemo<Screen>(() => {
    if (paymentFailed) return "failed";
    if (showCustomAmount && serverState === "idle") return "custom";
    return screenForState(serverState);
  }, [paymentFailed, serverState, showCustomAmount]);

  const amount = context.amount || lastOrder?.amount || 0;
  const price = context.price || lastOrder?.price || 0;
  const total = progress.total || amount;
  const current = serverState === "complete" ? amount : progress.current;

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
        setShowCustomAmount(false);
        if (message.payload.context.amount > 0) {
          setLastOrder({
            amount: message.payload.context.amount,
            price: message.payload.context.price,
          });
        }
        if (message.payload.state === "idle" || message.payload.state === "selected") {
          setProgress({ current: 0, total: 0 });
          setPaymentStarted(false);
        }
        if (message.payload.state === "complete") {
          setPaymentFailed(false);
          setFailureMessage("");
        }
        if (typeof message.payload.context.inventory === "number") {
          setInventory(message.payload.context.inventory);
        }
        if (message.payload.context.error && !isCancellationMessage(message.payload.context.error)) {
          setFailureMessage(message.payload.context.error);
        }
        break;
      case "PaymentStarted":
        setPaymentStarted(true);
        setPaymentFailed(false);
        setFailureMessage("");
        setStatusMessage("Betaling gestart");
        break;
      case "PaymentSucceeded":
        setPaymentStarted(false);
        setStatusMessage("Betaling ontvangen");
        break;
      case "PaymentFailed":
        setPaymentStarted(false);
        setPaymentFailed(true);
        setFailureMessage(message.payload.message);
        setStatusMessage(message.payload.message);
        break;
      case "PaymentCancelled":
        setPaymentStarted(false);
        setPaymentFailed(false);
        setFailureMessage("");
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
        setPaymentFailed(true);
        setFailureMessage(message.payload.message || "De hopper is leeg.");
        break;
      case "MachineReset":
        setPaymentStarted(false);
        setShowCustomAmount(false);
        setCustomInput("");
        if (message.payload.reason !== "recovery") {
          setPaymentFailed(false);
          setFailureMessage("");
        }
        setStatusMessage(
          message.payload.reason === "completed"
            ? "Klaar voor de volgende bestelling"
            : "Machine gereset"
        );
        break;
      case "ErrorOccurred":
        setPaymentStarted(false);
        setStatusMessage(message.payload.message);
        if (!isCancellationMessage(message.payload.message)) {
          setPaymentFailed(true);
          setFailureMessage(message.payload.message);
        }
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

  function selectAmount(selectedAmount: number) {
    setShowCustomAmount(false);
    setCustomInput("");
    sendCommand("SelectAmount", { amount: selectedAmount });
  }

  function resetToStart() {
    setPaymentFailed(false);
    setFailureMessage("");
    setShowCustomAmount(false);
    setCustomInput("");
    sendCommand("ResetMachine");
  }

  function cancelPayment() {
    setPaymentFailed(false);
    setFailureMessage("");
    sendCommand("CancelPayment");
  }

  function retryPayment() {
    const retryAmount = lastOrder?.amount || context.amount;
    if (!retryAmount) {
      resetToStart();
      return;
    }

    setPaymentFailed(false);
    setFailureMessage("");
    setPaymentStarted(false);
    sendCommand("SelectAmount", { amount: retryAmount });
    sendCommand("ConfirmSelection");
    sendCommand("StartPayment");
  }

  return (
    <div
      className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center select-none overflow-hidden"
      style={{ fontFamily: "var(--font-sans)" }}
    >
      {screen === "welcome" && (
        <WelcomeScreen
          connected={connected}
          inventory={inventory}
          presetAmounts={DEFAULT_PRESET_AMOUNTS}
          statusMessage={statusMessage}
          onSelectAmount={selectAmount}
          onCustomAmount={() => setShowCustomAmount(true)}
        />
      )}

      {screen === "custom" && (
        <CustomAmountScreen
          value={customInput}
          pricePerCoin={DEFAULT_PRICE_PER_COIN}
          onChange={setCustomInput}
          onSubmit={selectAmount}
          onBack={() => {
            setShowCustomAmount(false);
            setCustomInput("");
          }}
        />
      )}

      {screen === "confirm" && (
        <ConfirmScreen
          amount={amount}
          price={price}
          onBack={resetToStart}
          onConfirm={() => sendCommand("ConfirmSelection")}
        />
      )}

      {screen === "pay" && (
        <PaymentScreen
          amount={amount}
          price={price}
          paymentStarted={paymentStarted}
          statusMessage={statusMessage}
          onStartPayment={() => sendCommand("StartPayment")}
          onCancel={cancelPayment}
        />
      )}

      {screen === "failed" && (
        <PaymentFailedScreen
          message={failureMessage}
          onRetry={retryPayment}
          onBack={resetToStart}
        />
      )}

      {screen === "dispensing" && (
        <DispensingScreen current={current} total={total} />
      )}

      {screen === "thanks" && <ThanksScreen />}
    </div>
  );
}
