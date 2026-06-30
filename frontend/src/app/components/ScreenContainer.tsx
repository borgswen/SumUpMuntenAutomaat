import type { ReactNode } from "react";

type ScreenContainerProps = {
  children: ReactNode;
  maxWidth?: "sm" | "md" | "lg";
  status?: string;
};

const widths = {
  sm: "max-w-sm",
  md: "max-w-xl",
  lg: "max-w-2xl",
};

export function ScreenContainer({ children, maxWidth = "md", status }: ScreenContainerProps) {
  return (
    <main
      className={`w-full ${widths[maxWidth]} px-6 sm:px-10 flex flex-col items-center gap-8 sm:gap-10`}
    >
      {children}
      {status && <p className="min-h-7 text-center text-base sm:text-lg text-muted-foreground">{status}</p>}
    </main>
  );
}
