import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Filter, AlertTriangle, ChevronLeft, ChevronRight } from "lucide-react";
import { useSearchParams } from "react-router-dom";

import { bookings } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import {
  formatRub, formatDate, OTA_LABELS,
  PAYMENT_STATUS_LABELS, BOOKING_STATUS_LABELS,
} from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import type { OTASource, PaymentStatus, BookingStatus } from "@/types";

const OTA_OPTIONS: OTASource[] = ["yandex", "ostrovok", "bronevoy", "tinkoff", "2gis", "hotel101", "academservis"];

export default function BookingsPage() {
  const { currentHotel } = useHotel();
  const [searchParams] = useSearchParams();

  const [filters, setFilters] = useState({
    source_ota: [] as OTASource[],
    payment_status: [] as PaymentStatus[],
    booking_status: [] as BookingStatus[],
    guest_name: "",
    booking_id_ota: "",
    is_anomaly: searchParams.get("is_anomaly") === "true" ? true : undefined as boolean | undefined,
    page: 1,
    page_size: 50,
    sort_by: "check_in",
    sort_desc: true,
  });

  const { data, isLoading } = useQuery({
    queryKey: keys.bookings.list(currentHotel?.id ?? "", filters),
    queryFn: () => bookings.list(currentHotel!.id, filters),
    enabled: !!currentHotel,
  });

  const setFilter = (key: string, value: unknown) =>
    setFilters((f) => ({ ...f, [key]: value, page: 1 }));

  const paymentBadge = (status: string) => {
    const map: Record<string, "success" | "warning" | "destructive" | "info"> = {
      paid: "success", pending: "warning", cancelled: "destructive", refunded: "info",
    };
    return <Badge variant={map[status] || "secondary"}>{PAYMENT_STATUS_LABELS[status] || status}</Badge>;
  };

  const bookingBadge = (status: string) => {
    const map: Record<string, "success" | "warning" | "destructive"> = {
      confirmed: "success", cancelled: "destructive", no_show: "warning",
    };
    return <Badge variant={map[status] || "secondary"}>{BOOKING_STATUS_LABELS[status] || status}</Badge>;
  };

  if (!currentHotel) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Бронирования</h1>
        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total.toLocaleString("ru-RU")} записей
          </span>
        )}
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
                value={filters.guest_name}
                onChange={(e) => setFilter("guest_name", e.target.value)}
              />
            </div>
            <div className="relative flex-1 min-w-[160px]">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="ID брони..."
                className="pl-8"
                value={filters.booking_id_ota}
                onChange={(e) => setFilter("booking_id_ota", e.target.value)}
              />
            </div>
            <Select
              value={filters.source_ota[0] || "all"}
              onValueChange={(v) => setFilter("source_ota", v === "all" ? [] : [v])}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Все OTA" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все OTA</SelectItem>
                {OTA_OPTIONS.map((ota) => (
                  <SelectItem key={ota} value={ota}>{OTA_LABELS[ota]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filters.booking_status[0] || "all"}
              onValueChange={(v) => setFilter("booking_status", v === "all" ? [] : [v])}
            >
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
              variant={filters.is_anomaly ? "default" : "outline"}
              size="sm"
              className="h-9"
              onClick={() => setFilter("is_anomaly", filters.is_anomaly ? undefined : true)}
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
                  {["OTA", "ID брони", "Гость", "Тип номера", "Заезд", "Выезд", "Сумма гостя", "Комиссия", "%", "Чистая", "Статус оплаты", "Статус брони"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i} className="border-b">
                        {Array.from({ length: 12 }).map((_, j) => (
                          <td key={j} className="px-4 py-3"><Skeleton className="h-4 w-full" /></td>
                        ))}
                      </tr>
                    ))
                  : data?.items.map((b) => (
                      <tr
                        key={b.id}
                        className={`border-b hover:bg-muted/20 transition-colors ${b.is_anomaly ? "bg-red-50/50" : ""}`}
                      >
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="font-medium">{OTA_LABELS[b.source_ota] || b.source_ota}</span>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs whitespace-nowrap">
                          <div className="flex items-center gap-1">
                            {b.is_anomaly && <AlertTriangle className="h-3.5 w-3.5 text-red-500 shrink-0" />}
                            {b.booking_id_ota}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">{b.guest_name}</td>
                        <td className="px-4 py-3 text-muted-foreground">{b.room_type || "—"}</td>
                        <td className="px-4 py-3 tabular-nums whitespace-nowrap">{formatDate(b.check_in)}</td>
                        <td className="px-4 py-3 tabular-nums whitespace-nowrap">{formatDate(b.check_out)}</td>
                        <td className="px-4 py-3 tabular-nums text-right whitespace-nowrap">{formatRub(b.gross_amount)}</td>
                        <td className="px-4 py-3 tabular-nums text-right whitespace-nowrap text-red-600">{formatRub(b.ota_commission_amount)}</td>
                        <td className="px-4 py-3 tabular-nums text-right">{parseFloat(b.ota_commission_rate).toFixed(1)}%</td>
                        <td className="px-4 py-3 tabular-nums text-right whitespace-nowrap font-medium text-green-700">{formatRub(b.net_amount)}</td>
                        <td className="px-4 py-3">{paymentBadge(b.payment_status)}</td>
                        <td className="px-4 py-3">{bookingBadge(b.booking_status)}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <span className="text-sm text-muted-foreground">
                Стр. {data.page} из {data.total_pages}
              </span>
              <div className="flex gap-1">
                <Button
                  variant="outline" size="icon"
                  disabled={data.page <= 1}
                  onClick={() => setFilter("page", filters.page - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline" size="icon"
                  disabled={data.page >= data.total_pages}
                  onClick={() => setFilter("page", filters.page + 1)}
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
