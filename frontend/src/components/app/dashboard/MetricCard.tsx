import { cn, formatChange } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  change?: string | null;
  icon: LucideIcon;
  iconColor?: string;
  loading?: boolean;
  large?: boolean;
}

export function MetricCard({
  title, value, subtitle, change, icon: Icon, iconColor = "text-navy-600", loading, large,
}: MetricCardProps) {
  const ch = change !== undefined ? formatChange(change) : null;

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-3 flex-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-8 w-40" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-10 w-10 rounded-lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className={cn("tabular-nums font-bold text-foreground mt-1", large ? "text-3xl" : "text-2xl")}>
              {value}
            </p>
            {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
            {ch && (
              <div className={cn("flex items-center gap-1 mt-1.5 text-xs font-medium", ch.positive ? "text-green-600" : "text-red-500")}>
                {ch.positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {ch.text} к прошлому периоду
              </div>
            )}
          </div>
          <div className={cn("h-10 w-10 rounded-lg bg-muted flex items-center justify-center shrink-0 ml-4")}>
            <Icon className={cn("h-5 w-5", iconColor)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
