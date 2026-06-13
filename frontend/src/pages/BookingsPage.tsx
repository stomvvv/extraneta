import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, AlertTriangle, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { useSearchParams } from "react-router-dom";

import { bookings as bookingsApi } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import {
  formatRub, formatDate, OTA_LABELS, OTA_BADGE_CLASSES, BOOKING_STATUS_LABELS,
} from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const OTA_OPTIONS = Object.keys(OTA_LABELS);

const bookingBadgeVariant = (status: string) => {
  if (status === "confirmed") return "success";
  if (status === "cancelled") return "destructive";
  return "warning";
};

export default function BookingsPage() {
  const { currentHotel } = useHotel();
  const [searchParams] = useSearchParams();

  const [page, setPage] = useState(1);
  const [ota, setOta] = useState("");
  const [status, setStatus] = useState("");
  const [guest, setGuest] = useState("");
  const [isAnomaly, setIsAnomaly] = useState(
    searchParams.get("is_anomaly") === "true" ? true : undefined as boolean | undefined,
  );

  const filters = {
    hotel_id: currentHotel?.id,
    page,
    limit: 50,
    ota: ota || undefined,
    status: status || undefined,
    guest: guest || undefined,
    is_anomaly: isAnomaly,
  };

  const { data, isLoading } = useQuery({
    queryKey: keys.bookings.list(currentHotel?.id ?? null, filters),
    queryFn: () => bookingsApi.list(filters),
    enabled: !!currentHotel,
  });

  if (!currentHotel) return null;

  const exportUrl = bookingsApi.exportUrl(filters);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Бронирования</h1>
        <div className="flex items-center gap-2">
          {data && (
            <span className="text-sm text-muted-foreground">
              {data.total.toLocaleString("ru-RU")} записей
            </span>
          )}
          <Button variant="outline" size="sm" asChild>
            <a href={exportUrl} download>
              <Download className="h-4 w-4 mr-1.5" />
              Excel
            </a>
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4 pb-4">
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Имя гостя..."
                className="pl-8"
                value={guest}
                onChange={(e) => { setGuest(e.target.value); setPage(1); }}
              />
            </div>
            <Select value={ota || "all"} onValueChange={(v) => { setOta(v === "all" ? "" : v); setPage(1); }}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Все OTA" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все OTA</SelectItem>
                {OTA_OPTIONS.map((o) => (
                  <SelectItem key={o} value={o}>{OTA_LABELS[o]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status || "all"} onValueChange={(v) => { setStatus(v === "all" ? "" : v); setPage(1); }}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Статус" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все статусы</SelectItem>
                {Object.entries(BOOKING_STATUS_LABELS).map(([v, l]) => (
                  <SelectItem key={v} value={v}>{l}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant={isAnomaly ? "default" : "outline"}
              size="sm"
              className="h-9"
              onClick={() => { setIsAnomaly(isAnomaly ? undefined : true); setPage(1); }}
            >
              <AlertTriangle className="h-4 w-4 mr-1.5" />
              Аномалии
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/30">
                <tr>
                  {["OTA", "ID брони", "Гость", "Заезд", "Выезд", "Н", "Валовая", "Ком. %", "Ком. ₽", "Нетто", "Статус"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i} className="border-b">
                        {Array.from({ length: 11 }).map((_, j) => (
                          <td key={j} className="px-4 py-3"><Skeleton className="h-4 w-full" /></td>
                        ))}
                      </tr>
                    ))
                  : data?.items.map((b) => (
                      <tr
                        key={b.id}
                        className={`border-b hover:bg-muted/20 transition-colors ${b.has_anomaly ? "bg-red-50/50" : ""}`}
                      >
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${OTA_BADGE_CLASSES[b.source_ota] || "bg-gray-100 text-gray-800"}`}>
                            {OTA_LABELS[b.source_ota] || b.source_ota}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs whitespace-nowrap">
                          <div className="flex items-center gap-1">
                            {b.has_anomaly && <AlertTriangle className="h-3.5 w-3.5 text-red-500 shrink-0" title={b.anomaly_reason} />}
                            {b.booking_id_ota}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">{b.guest_name}</td>
                        <td className="px-4 py-3 tabular-nums whitespace-nowrap">{formatDate(b.check_in)}</td>
                        <td className="px-4 py-3 tabular-nums whitespace-nowrap">{formatDate(b.check_out)}</td>
                        <td className="px-4 py-3 tabular-nums text-center">{b.nights}</td>
                        <td className="px-4 py-3 tabular-nums text-right whitespace-nowrap">{formatRub(b.gross_amount)}</td>
                        <td className="px-4 py-3 tabular-nums text-right">{b.ota_commission_rate.toFixed(1)}%</td>
                        <td className="px-4 py-3 tabular-nums text-right whitespace-nowrap text-red-600">{formatRub(b.ota_commission_amount)}</td>
                        <td className="px-4 py-3 tabular-nums text-right whitespace-nowrap font-medium text-green-700">{formatRub(b.net_amount)}</td>
                        <td className="px-4 py-3">
                          <Badge variant={bookingBadgeVariant(b.booking_status) as any}>
                            {BOOKING_STATUS_LABELS[b.booking_status] || b.booking_status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>

          {data && data.pages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <span className="text-sm text-muted-foreground">
                Стр. {data.page} из {data.pages}
              </span>
              <div className="flex gap-1">
                <Button
                  variant="outline" size="icon"
                  disabled={data.page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline" size="icon"
                  disabled={data.page >= data.pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
