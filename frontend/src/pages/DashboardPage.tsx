import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { DollarSign, TrendingDown, BookOpen, CreditCard, Upload, AlertTriangle, Building2, Plus, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { hotels as hotelsApi } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { toast } from "@/hooks/use-toast";

import { analytics } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import {
  formatRub, formatPct, getPresetDates, toISODate, OTA_LABELS, OTA_COLORS,
} from "@/lib/utils";
import { MetricCard } from "@/components/app/dashboard/MetricCard";
import { PeriodSelector } from "@/components/app/dashboard/PeriodSelector";
import { ChannelTable } from "@/components/app/dashboard/ChannelTable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const { currentHotel, setCurrentHotelId } = useHotel();
  const navigate = useNavigate();

  const defaultPeriod = getPresetDates("current_month");
  const [dateFrom, setDateFrom] = useState(toISODate(defaultPeriod.from));
  const [dateTo, setDateTo] = useState(toISODate(defaultPeriod.to));

  const params = { date_from: dateFrom, date_to: dateTo };
  const enabled = !!currentHotel;

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: keys.analytics.summary(currentHotel?.id ?? "", params),
    queryFn: () => analytics.summary(currentHotel!.id, params),
    enabled,
  });

  const { data: channels = [], isLoading: channelsLoading } = useQuery({
    queryKey: keys.analytics.channels(currentHotel?.id ?? "", params),
    queryFn: () => analytics.channels(currentHotel!.id, params),
    enabled,
  });

  const { data: timeSeries = [], isLoading: tsLoading } = useQuery({
    queryKey: keys.analytics.timeSeries(currentHotel?.id ?? "", params),
    queryFn: () => analytics.timeSeries(currentHotel!.id, params),
    enabled,
  });

  const { data: anomalies } = useQuery({
    queryKey: keys.analytics.anomalies(currentHotel?.id ?? "", params),
    queryFn: () => analytics.anomalies(currentHotel!.id, params),
    enabled,
  });

  const hasData = (summary?.total_bookings ?? 0) > 0;
  const avgCommissionRate = summary ? parseFloat(summary.commission_rate_pct) : 0;

  const tsChartData = timeSeries.map((p) => ({
    period: p.period,
    "Валовая": parseFloat(p.gross_revenue),
    "Комиссии": parseFloat(p.commission_amount),
    "Чистая": parseFloat(p.net_revenue),
  }));

  const pieData = channels.map((ch) => ({
    name: OTA_LABELS[ch.source_ota] || ch.source_ota,
    value: parseFloat(ch.gross_revenue),
    ota: ch.source_ota,
  }));

  const handlePeriodChange = (from: string, to: string) => {
    setDateFrom(from);
    setDateTo(to);
  };

  const qc = useQueryClient();
  const [hotelName, setHotelName] = useState("");
  const [showForm, setShowForm] = useState(false);
  const createMutation = useMutation({
    mutationFn: (name: string) => hotelsApi.create({ name }),
    onSuccess: (h) => {
      qc.invalidateQueries({ queryKey: ["hotels"] });
      setCurrentHotelId(h.id);
      setHotelName("");
      setShowForm(false);
      toast({ title: `Отель "${h.name}" создан`, variant: "success" });
    },
    onError: (e: any) => toast({ title: "Ошибка", description: e.message, variant: "destructive" }),
  });

  if (!currentHotel) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center gap-4 py-16">
        <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
          <Building2 className="h-8 w-8 text-muted-foreground" />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Добро пожаловать в ExtranEta</h2>
          <p className="text-muted-foreground mt-1">Начните с добавления вашего первого отеля</p>
        </div>
        {!showForm ? (
          <Button onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Добавить отель
          </Button>
        ) : (
          <div className="flex gap-2 w-full max-w-sm">
            <Input
              autoFocus
              placeholder="Название отеля"
              value={hotelName}
              onChange={(e) => setHotelName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && hotelName.trim() && createMutation.mutate(hotelName.trim())}
            />
            <Button
              onClick={() => createMutation.mutate(hotelName.trim())}
              disabled={!hotelName.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Создать"}
            </Button>
            <Button variant="outline" onClick={() => { setShowForm(false); setHotelName(""); }}>
              Отмена
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{currentHotel.name}</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Финансовая аналитика по OTA-каналам</p>
        </div>
        <PeriodSelector onChange={handlePeriodChange} />
      </div>

      {/* Anomaly banner */}
      {anomalies && anomalies.total_anomalies > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3">
          <AlertTriangle className="h-4 w-4 text-yellow-600 shrink-0" />
          <p className="text-sm text-yellow-800">
            Обнаружено <strong>{anomalies.total_anomalies}</strong> аномалий за период.{" "}
          </p>
          <Button variant="outline" size="sm" className="ml-auto h-7 text-xs" onClick={() => navigate("/bookings?is_anomaly=true")}>
            Просмотреть
          </Button>
        </div>
      )}

      {/* Empty state */}
      {!hasData && !summaryLoading && (
        <div className="rounded-xl border-2 border-dashed border-muted-foreground/20 bg-muted/30 p-12 text-center">
          <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
          <h3 className="font-semibold text-lg">Нет данных за выбранный период</h3>
          <p className="text-muted-foreground mt-1 text-sm">
            Загрузите отчёты из OTA-экстранетов для отображения аналитики
          </p>
          <Button className="mt-4" onClick={() => navigate("/upload")}>
            Загрузить файлы
          </Button>
        </div>
      )}

      {/* KPI Cards */}
      {(hasData || summaryLoading) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <MetricCard
            title="Чистая выручка"
            value={summary ? formatRub(summary.net_revenue) : "—"}
            change={summary?.net_revenue_change_pct}
            icon={DollarSign}
            iconColor="text-green-600"
            loading={summaryLoading}
            large
          />
          <MetricCard
            title="Комиссии OTA"
            value={summary ? formatRub(summary.total_commission) : "—"}
            subtitle={summary ? `${formatPct(summary.commission_rate_pct)} от выручки` : undefined}
            icon={TrendingDown}
            iconColor="text-red-500"
            loading={summaryLoading}
          />
          <MetricCard
            title="Бронирования"
            value={summary ? String(summary.total_bookings) : "—"}
            subtitle={summary ? `${summary.confirmed_bookings} подтверждено, ${summary.cancelled_bookings} отменено` : undefined}
            change={summary?.bookings_change_pct}
            icon={BookOpen}
            iconColor="text-blue-600"
            loading={summaryLoading}
          />
          <MetricCard
            title="Средний чек"
            value={summary ? formatRub(summary.avg_booking_value) : "—"}
            subtitle={summary?.occupancy_pct ? `Загрузка: ${parseFloat(summary.occupancy_pct).toFixed(1)}%` : undefined}
            icon={CreditCard}
            iconColor="text-purple-600"
            loading={summaryLoading}
          />
        </div>
      )}

      {/* Charts row */}
      {(hasData || summaryLoading) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Stacked bar: revenue vs commissions */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Выручка и комиссии</CardTitle>
            </CardHeader>
            <CardContent>
              {tsLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={tsChartData} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v: number) => formatRub(v)} />
                    <Legend />
                    <Bar dataKey="Чистая" stackId="a" fill="#1E3A5F" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="Комиссии" stackId="a" fill="#EF4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Pie: channel share */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Доля каналов</CardTitle>
            </CardHeader>
            <CardContent>
              {channelsLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) => `${name.split(" ")[0]} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {pieData.map((entry) => (
                        <Cell key={entry.ota} fill={OTA_COLORS[entry.ota] || "#94a3b8"} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: number) => formatRub(v)} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-muted-foreground">Нет данных</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Net revenue line chart */}
      {(hasData || summaryLoading) && timeSeries.length > 1 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Динамика чистой выручки</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={tsChartData} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number) => formatRub(v)} />
                <Line type="monotone" dataKey="Чистая" stroke="#1E3A5F" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Channel breakdown table */}
      {(hasData || channelsLoading) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Сравнение каналов</CardTitle>
          </CardHeader>
          <CardContent>
            <ChannelTable data={channels} loading={channelsLoading} avgCommissionRate={avgCommissionRate} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
