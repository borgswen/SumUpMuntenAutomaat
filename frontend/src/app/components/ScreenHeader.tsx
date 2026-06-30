import type { ReactNode } from "react";

type ScreenHeaderProps = {
  icon?: ReactNode;
  title: ReactNode;
  subtitle?: ReactNode;
};

export function ScreenHeader({ icon, title, subtitle }: ScreenHeaderProps) {
  return (
    <div className="flex flex-col items-center gap-4 text-center">
      {icon}
      <h1
        className="text-center text-5xl font-extrabold uppercase text-foreground sm:text-6xl"
        style={{ fontFamily: "var(--font-heading)", letterSpacing: "0.05em", lineHeight: 1 }}
      >
        {title}
      </h1>
      {subtitle && <p className="text-xl tracking-wide text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
