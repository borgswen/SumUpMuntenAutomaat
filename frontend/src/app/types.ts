export type Screen =
  | "welcome"
  | "custom"
  | "confirm"
  | "pay"
  | "failed"
  | "dispensing"
  | "thanks";

export type BackendState =
  | "idle"
  | "selected"
  | "awaiting_payment"
  | "payment_authorized"
  | "dispensing"
  | "complete"
  | "error";

export type MachineContext = {
  amount: number;
  price: number;
  transaction_id?: string | null;
  error?: string | null;
  inventory?: number | null;
  dispensed?: number;
};

export type BackendEvent =
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

export type CommandType =
  | "SelectAmount"
  | "ConfirmSelection"
  | "StartPayment"
  | "CancelPayment"
  | "ResetMachine";

export type ProgressState = {
  current: number;
  total: number;
};
