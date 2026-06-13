import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, FileIcon, CheckCircle2, XCircle, Loader2, Clock, Trash2,
} from "lucide-react";

import { uploads as uploadsApi } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import { toast } from "@/hooks/use-toast";
import { formatDateTime, OTA_LABELS } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const OTA_OPTIONS = [
  { value: "yandex", label: "Яндекс Путешествия" },
  { value: "ostrovok", label: "Ostrovok.ru" },
  { value: "bronevic", label: "Броневик" },
  { value: "tinkoff", label: "Тинькофф Путешествия" },
  { value: "2gis", label: "2ГИС" },
  { value: "101hotel", label: "101отель" },
  { value: "academservis", label: "Academservis" },
  { value: "auto", label: "Автоопределение" },
];

interface PendingFile {
  file: File;
  ota: string;
}

const statusBadge = (status: string) => {
  switch (status) {
    case "done": return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" />Готово</Badge>;
    case "error": return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Ошибка</Badge>;
    case "processing": return <Badge variant="warning"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Обработка</Badge>;
    default: return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />—</Badge>;
  }
};

export default function UploadPage() {
  const { currentHotel } = useHotel();
  const qc = useQueryClient();
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const { data: uploadList = [], isLoading } = useQuery({
    queryKey: keys.uploads.list(currentHotel?.id ?? null),
    queryFn: () => uploadsApi.list(currentHotel!.id),
    enabled: !!currentHotel,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => uploadsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.uploads.list(currentHotel?.id ?? null) });
      qc.invalidateQueries({ queryKey: keys.dashboard.data(currentHotel?.id ?? null) });
      toast({ title: "Загрузка удалена", variant: "success" });
    },
  });

  const onDrop = useCallback((accepted: File[]) => {
    setPendingFiles((prev) => [
      ...prev,
      ...accepted.map((file) => ({ file, ota: "" })),
    ]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
    },
    maxFiles: 10,
  });

  const handleUploadAll = async () => {
    const valid = pendingFiles.filter((p) => p.ota);
    if (!valid.length) {
      toast({ title: "Выберите OTA для каждого файла", variant: "destructive" });
      return;
    }
    setUploading(true);
    let success = 0;
    for (const { file, ota } of valid) {
      try {
        await uploadsApi.upload(file, ota, currentHotel?.id);
        success++;
      } catch (err: any) {
        toast({ title: `Ошибка: ${file.name}`, description: err.message, variant: "destructive" });
      }
    }
    setUploading(false);
    if (success > 0) {
      setPendingFiles([]);
      qc.invalidateQueries({ queryKey: keys.uploads.list(currentHotel?.id ?? null) });
      qc.invalidateQueries({ queryKey: keys.dashboard.data(currentHotel?.id ?? null) });
      toast({ title: `Загружено ${success} файл(ов)`, variant: "success" });
    }
  };

  if (!currentHotel) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Загрузка файлов</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Загрузить отчёты</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
              isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/30 hover:border-primary/50"
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
            <p className="font-medium">Перетащите файлы сюда или нажмите для выбора</p>
            <p className="text-sm text-muted-foreground mt-1">
              Поддерживается: .xlsx, .xls, .csv — до 10 файлов
            </p>
          </div>

          {pendingFiles.length > 0 && (
            <div className="space-y-2">
              {pendingFiles.map((pf, i) => (
                <div key={i} className="flex items-center gap-3 rounded-lg border p-3 bg-muted/30">
                  <FileIcon className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="text-sm flex-1 truncate">{pf.file.name}</span>
                  <Select
                    value={pf.ota}
                    onValueChange={(v) =>
                      setPendingFiles((prev) =>
                        prev.map((p, j) => (j === i ? { ...p, ota: v } : p)),
                      )
                    }
                  >
                    <SelectTrigger className="w-52 h-7 text-xs">
                      <SelectValue placeholder="Выберите OTA..." />
                    </SelectTrigger>
                    <SelectContent>
                      {OTA_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    variant="ghost" size="icon" className="h-7 w-7 shrink-0"
                    onClick={() => setPendingFiles((prev) => prev.filter((_, j) => j !== i))}
                  >
                    <XCircle className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </div>
              ))}
              <div className="flex justify-between items-center pt-2">
                <Button variant="outline" size="sm" onClick={() => setPendingFiles([])}>
                  Очистить
                </Button>
                <Button onClick={handleUploadAll} disabled={uploading}>
                  {uploading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Загрузить {pendingFiles.filter((p) => p.ota).length} файл(ов)
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">История загрузок</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-14 rounded-lg" />)}
            </div>
          ) : uploadList.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground text-sm">
              Нет загрузок — добавьте первый файл выше
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/30">
                <tr>
                  {["Файл", "OTA", "Статус", "Добавлено", "Пропущено", "Дата", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-medium text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {uploadList.map((u) => (
                  <tr key={u.id} className="border-b hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileIcon className="h-4 w-4 text-muted-foreground shrink-0" />
                        <p className="font-medium truncate max-w-48">{u.filename}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">{OTA_LABELS[u.ota] || u.ota}</td>
                    <td className="px-4 py-3">
                      {statusBadge(u.status)}
                      {u.status === "error" && u.error_message && (
                        <p className="text-xs text-red-600 mt-1 max-w-48 truncate" title={u.error_message}>
                          {u.error_message}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 tabular-nums">{u.records_added}</td>
                    <td className="px-4 py-3 tabular-nums text-muted-foreground">{u.records_skipped}</td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatDateTime(u.uploaded_at)}</td>
                    <td className="px-4 py-3">
                      <Button
                        variant="ghost" size="icon" className="h-7 w-7 text-red-500 hover:text-red-700"
                        onClick={() => {
                          if (confirm("Удалить загрузку и все связанные бронирования?")) {
                            deleteMutation.mutate(u.id);
                          }
                        }}
                        title="Удалить"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
