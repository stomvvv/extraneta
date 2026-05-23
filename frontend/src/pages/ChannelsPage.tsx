import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";

import { analytics } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import { formatRub, formatPct, getPresetDates, toISODate, OTA_LABELS, OTA_COLORS } from "@/lib/utils";
import { PeriodSelector } from "@/components/app/dashboard/PeriodSelector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function ChannelsPage() {
  const { currentHotel } = useHotel();
  const defaultPeriod = getPresetDates("current_month");
  const [dateFrom, setDateFrom] = useState(toISODate(defaultPeriod.from));
  const [dateTo, setDateTo] = useState(toISODate(defaultPeriod.to));

  const params = { date_from: dateFrom, date_to: dateTo };
  const enabled = !!currentHotel;

  const { data: channels = [], isLoading } = useQuery({
    queryKey: keys.analytics.channels(currentHotel?.id ?? "", params),
    queryFn: () => analytics.channels(currentHotel!.id, params),
    enabled,
  });

  const barData = channels.map((ch) => ({
    name: OTA_LABELS[ch.source_ota] || ch.source_ota,
    ota: ch.source_ota,
    "Чистая выручка": parseFloat(ch.net_revenue),
    "Комиссии": parseFloat(ch.commission_amount),
    "% комиссии": parseFloat(ch.commission_rate_pct),
  }));

  if (!currentHotel) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold">Анализ по каналам</h1>
        <PeriodSelector onChange={(from, to) => { setDateFrom(from); setDateTo(to); }} />
      </div>

      {/* Channel cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40 rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {channels.map((ch) => {
            const color = OTA_COLORS[ch.source_ota] || "#94a3b8";
            return (
              <Card key={ch.source_ota} className="hover:shadow-md transition-shadow">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                    <span className="font-semibold text-sm">{OTA_LABELS[ch.source_ota] || ch.source_ota}</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Броней</span>
                      <span className="font-medium">{ch.bookings_count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Валовая</span>
                      <span className="font-medium tabular-nums">{formatRub(ch.gross_revenue)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Комиссия</span>
                      <span className="font-medium text-red-600 tabular-nums">{formatRub(ch.commission_amount)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">% комиссии</span>
                      <span className="font-medium">{formatPct(ch.commission_rate_pct)}</span>
                    </div>
                    <div className="pt-1 border-t flex justify-between text-sm">
                      <span className="text-muted-foreground">Чистая</span>
                      <span className="font-bold text-green-700 tabular-nums">{formatRub(ch.net_revenue)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Доля</span>
                      <span className="font-medium">{parseFloat(ch.channel_share_pct).toFixed(1)}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Grouped bar chart */}
      {!isLoading && barData.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Выручка по каналам</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={barData} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number) => formatRub(v)} />
                <Legend />
                <Bar dataKey="Чистая выручка" fill="#1E3A5F" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Комиссии" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Commission rate comparison */}
      {!isLoading && barData.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Ставки комиссии по каналам</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} layout="vertical" margin={{ top: 4, right: 40, bottom: 4, left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} domain={[0, "auto"]} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} />
                <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} />
                <Bar dataKey="% комиссии" radius={[0, 4, 4, 0]}>
                  {barData.map((entry) => (
                    <Cell key={entry.ota} fill={OTA_COLORS[entry.ota] || "#94a3b8"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {!isLoading && channels.length === 0 && (
        <div className="text-center py-16 text-muted-foreground">
          Нет данных за выбранный период
        </div>
      )}
    </div>
  );
}
