interface HourlyChartProps {
  data: number[];
}

export function HourlyChart({ data }: HourlyChartProps) {
  const max = Math.max(...data);

  return (
    <div className="flex flex-col gap-px">
      {data.map((value, hour) => {
        const pct = (value / max) * 100;
        return (
          <div key={hour} className="flex items-center gap-1">
            <span className="w-10 text-[10px] text-gray-400">
              {String(hour).padStart(2, "0")}:00
            </span>
            <div className="flex-1 h-1.5 bg-gray-50 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-400 rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
