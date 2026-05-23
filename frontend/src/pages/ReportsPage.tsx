import { useState } from "react";
import { FileSpreadsheet, FileText, Download, Loader2 } from "lucide-react";
import { reports } from "@/lib/api";
import { useHotel } from "@/hooks/use-hotel";
import { getPresetDates, toISODate } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import { PeriodSelector } from "@/components/app/dashboard/PeriodSelector";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ReportsPage() {
  const { currentHotel } = useHotel();
  const defaultPeriod = getPresetDates("current_month");
  const [dateFrom, setDateFrom] = useState(toISODate(defaultPeriod.from));
  const [dateTo, setDateTo] = useState(toISODate(defaultPeriod.to));

  const [downloading, setDownloading] = useState<string | null>(null);

  if (!currentHotel) return null;

  const handleDownload = async (url: string, filename: string) => {
    setDownloading(filename);
    try {
      const resp = await fetch(url);
      if (!resp.ok) {
        toast({ title: "Ошибка при скачивании", description: `HTTP ${resp.status}`, variant: "destructive" });
        return;
      }
      const blob = await resp.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(blobUrl);
    } catch (e: any) {
      toast({ title: "Ошибка при скачивании", description: e.message, variant: "destructive" });
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold">Экспорт отчётов</h1>
        <PeriodSelector onChange={(from, to) => { setDateFrom(from); setDateTo(to); }} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Excel report */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-green-100 flex items-center justify-center">
                <FileSpreadsheet className="h-5 w-5 text-green-700" />
              </div>
              <div>
                <CardTitle className="text-base">Excel-отчёт (.xlsx)</CardTitle>
                <CardDescription>Полная детализация с формулами</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-1 mb-4">
              <li>• Лист 1: Сводные показатели</li>
              <li>• Лист 2: Разбивка по каналам</li>
              <li>• Лист 3: Все бронирования</li>
              <li>• Лист 4: Аномалии и флаги</li>
            </ul>
            <Button
              className="w-full"
              variant="outline"
              disabled={!!downloading}
              onClick={() => handleDownload(
                reports.excelUrl(currentHotel.id, dateFrom, dateTo),
                `extraneta_${dateFrom}_${dateTo}.xlsx`,
              )}
            >
              {downloading?.endsWith(".xlsx") ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Download className="h-4 w-4 mr-2" />}
              Скачать Excel
            </Button>
          </CardContent>
        </Card>

        {/* PDF report */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-red-100 flex items-center justify-center">
                <FileText className="h-5 w-5 text-red-700" />
              </div>
              <div>
                <CardTitle className="text-base">PDF-отчёт</CardTitle>
                <CardDescription>Управленческая сводка</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-muted-foreground space-y-1 mb-4">
              <li>• Ключевые показатели за период</li>
              <li>• Таблица по каналам</li>
              <li>• Топ-5 броней по стоимости</li>
              <li>• Выявленные аномалии</li>
            </ul>
            <Button
              className="w-full"
              variant="outline"
              disabled={!!downloading}
              onClick={() => handleDownload(
                reports.pdfUrl(currentHotel.id, dateFrom, dateTo),
                `extraneta_${dateFrom}_${dateTo}.pdf`,
              )}
            >
              {downloading?.endsWith(".pdf") ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Download className="h-4 w-4 mr-2" />}
              Скачать PDF
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
