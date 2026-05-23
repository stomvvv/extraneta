import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn, getPresetDates, toISODate, type PresetPeriod } from "@/lib/utils";

interface PeriodSelectorProps {
  onChange: (from: string, to: string) => void;
}

const PRESETS: { key: PresetPeriod; label: string }[] = [
  { key: "current_month", label: "Текущий месяц" },
  { key: "last_month", label: "Прошлый месяц" },
  { key: "last_30", label: "30 дней" },
  { key: "current_quarter", label: "Квартал" },
];

export function PeriodSelector({ onChange }: PeriodSelectorProps) {
  const [active, setActive] = useState<PresetPeriod>("current_month");

  const handlePreset = (preset: PresetPeriod) => {
    setActive(preset);
    const { from, to } = getPresetDates(preset);
    onChange(toISODate(from), toISODate(to));
  };

  return (
    <div className="flex flex-wrap gap-1.5">
      {PRESETS.map(({ key, label }) => (
        <Button
          key={key}
          variant={active === key ? "default" : "outline"}
          size="sm"
          onClick={() => handlePreset(key)}
          className="h-7 text-xs"
        >
          {label}
        </Button>
      ))}
    </div>
  );
}
