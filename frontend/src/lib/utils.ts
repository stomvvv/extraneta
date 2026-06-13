import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, startOfMonth, endOfMonth, subMonths, startOfQuarter, endOfQuarter } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRub(value: string | number, compact = false): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "—";
  if (compact && Math.abs(num) >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)} млн ₽`;
  }
  if (compact && Math.abs(num) >= 1_000) {
    return `${(num / 1_000).toFixed(0)} тыс ₽`;
  }
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatPct(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "—";
  return `${num.toFixed(2)}%`;
}

export function formatChange(value: string | number | null | undefined): {
  text: string;
  positive: boolean;
} {
  if (value === null || value === undefined) return { text: "—", positive: true };
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return { text: "—", positive: true };
  const sign = num >= 0 ? "+" : "";
  return { text: `${sign}${num.toFixed(1)}%`, positive: num >= 0 };
}

export function formatDate(iso: string): string {
  return format(new Date(iso), "dd.MM.yyyy");
}

export function formatDateTime(iso: string): string {
  return format(new Date(iso), "dd.MM.yyyy HH:mm");
}

export function formatDateRange(from: Date, to: Date): string {
  return `${format(from, "dd.MM.yyyy")} — ${format(to, "dd.MM.yyyy")}`;
}

export function toISODate(d: Date): string {
  return format(d, "yyyy-MM-dd");
}

export type PresetPeriod = "current_month" | "last_month" | "last_30" | "current_quarter" | "custom";

export function getPresetDates(preset: PresetPeriod): { from: Date; to: Date } {
  const today = new Date();
  switch (preset) {
    case "current_month":
      return { from: startOfMonth(today), to: endOfMonth(today) };
    case "last_month": {
      const last = subMonths(today, 1);
      return { from: startOfMonth(last), to: endOfMonth(last) };
    }
    case "last_30":
      return { from: new Date(today.getTime() - 30 * 86400_000), to: today };
    case "current_quarter":
      return { from: startOfQuarter(today), to: endOfQuarter(today) };
    default:
      return { from: startOfMonth(today), to: endOfMonth(today) };
  }
}

export const OTA_LABELS: Record<string, string> = {
  yandex: "Яндекс Путешествия",
  ostrovok: "Ostrovok.ru",
  bronevic: "Броневик",
  tinkoff: "Тинькофф",
  "2gis": "2ГИС",
  "101hotel": "101отель",
  academservis: "Academservis",
};

export const OTA_BADGE_CLASSES: Record<string, string> = {
  yandex: "bg-red-100 text-red-800",
  ostrovok: "bg-blue-100 text-blue-800",
  bronevic: "bg-orange-100 text-orange-800",
  tinkoff: "bg-yellow-100 text-yellow-800",
  "2gis": "bg-green-100 text-green-800",
  "101hotel": "bg-purple-100 text-purple-800",
  academservis: "bg-gray-100 text-gray-800",
};

export const OTA_COLORS: Record<string, string> = {
  yandex: "#FF0000",
  ostrovok: "#0066CC",
  bronevic: "#FF6B00",
  tinkoff: "#FFDD2D",
  "2gis": "#00B956",
  "101hotel": "#9B59B6",
  academservis: "#1ABC9C",
};

export const PAYMENT_STATUS_LABELS: Record<string, string> = {
  paid: "Оплачено",
  pending: "Ожидает",
  cancelled: "Отменено",
  refunded: "Возврат",
};

export const BOOKING_STATUS_LABELS: Record<string, string> = {
  confirmed: "Подтверждена",
  cancelled: "Отменена",
  no_show: "Неявка",
};

export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
}
