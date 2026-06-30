import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function PrimaryButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`rounded-2xl bg-primary px-8 py-5 text-primary-foreground shadow-lg transition-all duration-150 hover:brightness-110 active:scale-95 disabled:cursor-not-allowed disabled:opacity-35 ${className}`}
      style={{
        fontFamily: "var(--font-heading)",
        fontSize: "1.5rem",
        fontWeight: 800,
        boxShadow: props.disabled ? "none" : "0 8px 32px rgba(245,166,35,0.25)",
      }}
      {...props}
    >
      {children}
    </button>
  );
}

export function SecondaryButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`rounded-2xl border-2 border-border bg-secondary/35 px-8 py-5 text-foreground transition-all duration-150 hover:border-primary/50 hover:text-primary active:scale-95 disabled:cursor-not-allowed disabled:opacity-35 ${className}`}
      style={{
        fontFamily: "var(--font-heading)",
        fontSize: "1.35rem",
        fontWeight: 700,
      }}
      {...props}
    >
      {children}
    </button>
  );
}

export function AmountButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`rounded-2xl bg-primary py-9 text-primary-foreground transition-all duration-150 hover:brightness-110 active:scale-95 disabled:cursor-not-allowed disabled:opacity-35 ${className}`}
      style={{
        fontFamily: "var(--font-heading)",
        fontSize: "5rem",
        fontWeight: 800,
        lineHeight: 1,
        boxShadow: props.disabled ? "none" : "0 8px 32px rgba(245,166,35,0.25)",
      }}
      {...props}
    >
      {children}
    </button>
  );
}

export function NumpadButton({ children, className = "", ...props }: ButtonProps) {
  const isClear = children === "C";
  return (
    <button
      className={`rounded-2xl py-5 transition-all duration-100 active:scale-95 ${
        isClear
          ? "bg-destructive/20 text-destructive hover:bg-destructive/30"
          : "bg-secondary text-secondary-foreground hover:brightness-125"
      } ${className}`}
      style={{
        fontFamily: "var(--font-heading)",
        fontSize: "2rem",
        fontWeight: 700,
      }}
      {...props}
    >
      {children}
    </button>
  );
}
