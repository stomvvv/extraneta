import { formatRub, formatPct, OTA_LABELS, OTA_COLORS } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface Props {
  data: any[];
  loading: boolean;
  avgCommissionRate: number;
}

export function ChannelTable({ data, loading, avgCommissionRate }: Props) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (!data.length) {
    return <p className="text-sm text-muted-foreground">Нет данных за выбранный период</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-muted-foreground">
            <th className="text-left py-2 font-medium">Канал</th>
            <th className="text-right py-2 font-medium">Броней</th>
            <th className="text-right py-2 font-medium">Валовая</th>
            <th className="text-right py-2 font-medium">Комиссия</th>
            <th className="text-right py-2 font-medium">%</th>
            <th className="text-right py-2 font-medium">Чистая</th>
            <th className="text-right py-2 font-medium">Доля</th>
          </tr>
        </thead>
        <tbody>
          {data.map((ch) => {
            const rate = Number(ch.real_commission_rate ?? ch.commission_rate_pct ?? 0);
            const isAboveAvg = rate > avgCommissionRate + 0.5;
            const isBelowAvg = rate < avgCommissionRate - 0.5;
            const share = Number(ch.share_pct ?? ch.channel_share_pct ?? 0);
            return (
              <tr key={ch.source_ota} className="border-b hover:bg-muted/30 transition-colors">
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: OTA_COLORS[ch.source_ota] || "#94a3b8" }}
                    />
                    <span className="font-medium">{ch.ota_name || OTA_LABELS[ch.source_ota] || ch.source_ota}</span>
                  </div>
                </td>
                <td className="text-right py-3 tabular-nums">{ch.bookings ?? ch.bookings_count ?? 0}</td>
                <td className="text-right py-3 tabular-nums">{formatRub(ch.gross_revenue)}</td>
                <td className="text-right py-3 tabular-nums">{formatRub(ch.commission_amount)}</td>
                <td className="text-right py-3">
                  <span className={isAboveAvg ? "text-red-600 font-medium" : isBelowAvg ? "text-green-600 font-medium" : ""}>
                    {formatPct(rate)}
                  </span>
                </td>
                <td className="text-right py-3 tabular-nums">{formatRub(ch.net_revenue)}</td>
                <td className="text-right py-3">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 bg-muted rounded-full h-1.5">
                      <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${Math.min(share, 100)}%` }} />
                    </div>
                    <span className="tabular-nums text-xs w-10 text-right">{share.toFixed(1)}%</span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
