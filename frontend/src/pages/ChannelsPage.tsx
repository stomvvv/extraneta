import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";
import { CheckCircle2, AlertTriangle } from "lucide-react";

import { channels as channelsApi } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import { formatRub, formatPct, getPresetDates, toISODate, OTA_COLORS } from "@/lib/utils";
import { PeriodSelector } from "@/components/app/dashboard/PeriodSelector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function ChannelsPage() {
  const { currentHotel } = useHotel();
  const defaultPeriod = getPresetDates("last_30");
  const [dateFrom, setDateFrom] = useState(toISODate(defaultPeriod.from));
  const [dateTo, setDateTo] = useState(toISODate(defaultPeriod.to));

  const params = { hotel_id: currentHotel?.id, date_from: dateFrom, date_to: dateTo };

  const { data: channelList = [], isLoading } = useQuery({
    queryKey: keys.channels.list(currentHotel?.id ?? null, params),
    queryFn: () => channelsApi.list(params),
    enabled: !!currentHotel,
  });

  const barData = channelList.map((ch) => ({
    name: ch.ota_name || ch.source_ota,
    ota: ch.source_ota,
    "Чистая выручка": ch.net_revenue,
    "Комиссии": ch.commission_amount,
    "% комиссии": ch.real_commission_rate,
  }));

  if (!currentHotel) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold">Анализ по каналам</h1>
        <PeriodSelector onChange={(from, to) => { setDateFrom(from); setDateTo(to); }} />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-52 rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {channelList.map((ch) => {
            const color = OTA_COLORS[ch.source_ota] || "#94a3b8";
            const isOk = ch.status === "ok";
            return (
              <Card key={ch.source_ota} className="hover:shadow-md transition-shadow">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                      <span className="font-semibold text-sm">{ch.ota_name}</span>
                    </div>
                    {isOk
                      ? <CheckCircle2 className="h-4 w-4 text-green-500" title="Комиссия в норме" />
                      : <AlertTriangle className="h-4 w-4 text-yellow-500" title={`Отклонение комиссии: ${ch.deviation.toFixed(1)}%`} />
                    }
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Броней</span>
                      <span className="font-medium">{ch.bookings}</span>
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
                      <span className="text-muted-foreground">Реальный %</span>
                      <span className={`font-medium ${isOk ? "" : "text-yellow-600"}`}>
                        {ch.real_commission_rate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Ожидаемый %</span>
                      <span className="font-medium text-muted-foreground">{ch.expected_commission_rate.toFixed(1)}%</span>
                    </div>
                    <div className="pt-1 border-t flex justify-between text-sm">
                      <span className="text-muted-foreground">Чистая</span>
                      <span className="font-bold text-green-700 tabular-nums">{formatRub(ch.net_revenue)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Доля</span>
                      <span className="font-medium">{ch.share_pct.toFixed(1)}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

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

      {!isLoading && channelList.length === 0 && (
        <div className="text-center py-16 text-muted-foreground">
          Нет данных за выбранный период
        </div>
      )}
    </div>
  );
}
