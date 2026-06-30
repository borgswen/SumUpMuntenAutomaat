type ProgressBarProps = {
  current: number;
  total: number;
};

export function ProgressBar({ current, total }: ProgressBarProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className="w-full flex flex-col gap-4">
      <div className="h-7 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full bg-primary transition-all duration-75"
          style={{
            width: `${percentage}%`,
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
        <span>{percentage}%</span>
      </div>
    </div>
  );
}
