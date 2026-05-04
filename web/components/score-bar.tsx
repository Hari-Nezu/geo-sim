interface ScoreBarProps {
  label: string;
  value: number;
  max: number;
  color: "blue" | "green" | "orange";
}

const colorClasses = {
  blue: "bg-blue-500",
  green: "bg-green-500",
  orange: "bg-orange-500",
};

export function ScoreBar({ label, value, max, color }: ScoreBarProps) {
  const pct = (value / max) * 100;
  const display = max === 100 ? `${value.toFixed(0)}%` : value.toFixed(1);

  return (
    <div className="flex items-center gap-2 mb-1">
      <span className="w-24 text-xs text-gray-700 shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${colorClasses[color]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-xs text-gray-500">{display}</span>
    </div>
  );
}
