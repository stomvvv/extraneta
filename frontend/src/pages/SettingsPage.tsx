import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Loader2, Trash2 } from "lucide-react";

import { hotels as hotelsApi, settings as settingsApi } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import { toast } from "@/hooks/use-toast";
import { OTA_LABELS } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

const OTA_KEYS = Object.keys(OTA_LABELS);

export default function SettingsPage() {
  const { currentHotel, setCurrentHotelId, hotels } = useHotel();
  const qc = useQueryClient();

  const [hotelName, setHotelName] = useState(currentHotel?.name ?? "");
  const [newHotelName, setNewHotelName] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [rates, setRates] = useState<Record<string, string>>({});
  const [confirmClear, setConfirmClear] = useState(false);

  // Commission settings from API
  const { data: commissions = [] } = useQuery({
    queryKey: keys.settings.commissions(currentHotel?.id ?? null),
    queryFn: () => settingsApi.getCommissions(currentHotel!.id),
    enabled: !!currentHotel,
  });

  // Sync rates when commissions load
  useEffect(() => {
    if (commissions.length > 0) {
      const r: Record<string, string> = {};
      for (const c of commissions) {
        r[c.ota] = String(c.expected_rate);
      }
      setRates(r);
    }
  }, [commissions]);

  // Sync hotel name
  useEffect(() => {
    if (currentHotel) setHotelName(currentHotel.name);
  }, [currentHotel?.id]);

  const updateHotelMutation = useMutation({
    mutationFn: () => hotelsApi.update(currentHotel!.id, { name: hotelName.trim() }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.hotels.all() });
      toast({ title: "Отель обновлён", variant: "success" });
    },
    onError: (e: any) => toast({ title: "Ошибка", description: e.message, variant: "destructive" }),
  });

  const saveRatesMutation = useMutation({
    mutationFn: () => {
      const updates = OTA_KEYS
        .filter((ota) => rates[ota] !== undefined)
        .map((ota) => ({ ota, expected_rate: parseFloat(rates[ota] || "0") }))
        .filter((u) => !isNaN(u.expected_rate));
      return settingsApi.updateCommissions(updates, currentHotel!.id);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.settings.commissions(currentHotel?.id ?? null) });
      toast({ title: "Ставки сохранены", variant: "success" });
    },
    onError: (e: any) => toast({ title: "Ошибка", description: e.message, variant: "destructive" }),
  });

  const createMutation = useMutation({
    mutationFn: () => hotelsApi.create({ name: newHotelName.trim() }),
    onSuccess: (h) => {
      qc.invalidateQueries({ queryKey: keys.hotels.all() });
      setCurrentHotelId(h.id);
      setNewHotelName("");
      setShowCreate(false);
      toast({ title: `Отель "${h.name}" создан`, variant: "success" });
    },
    onError: (e: any) => toast({ title: "Ошибка", description: e.message, variant: "destructive" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => hotelsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.hotels.all() });
      toast({ title: "Отель удалён" });
    },
    onError: (e: any) => toast({ title: "Ошибка", description: e.message, variant: "destructive" }),
  });

  const clearMutation = useMutation({
    mutationFn: () => settingsApi.clearData(currentHotel!.id),
    onSuccess: () => {
      qc.invalidateQueries();
      setConfirmClear(false);
      toast({ title: "Данные очищены" });
    },
  });

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold">Настройки</h1>

      {/* Current hotel */}
      {currentHotel && (
        <Card>
          <CardHeader>
            <CardTitle>Текущий отель</CardTitle>
            <CardDescription>Основные параметры</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <Input
                value={hotelName}
                onChange={(e) => setHotelName(e.target.value)}
                placeholder="Название отеля"
                className="flex-1"
              />
              <Button
                onClick={() => updateHotelMutation.mutate()}
                disabled={!hotelName.trim() || updateHotelMutation.isPending}
              >
                {updateHotelMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Сохранить
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Commission settings */}
      {currentHotel && (
        <Card>
          <CardHeader>
            <CardTitle>Ожидаемые ставки комиссий</CardTitle>
            <CardDescription>
              Используются для выявления аномалий. Отклонение &gt;1% считается аномалией.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {OTA_KEYS.map((ota) => (
                <div key={ota} className="flex items-center gap-2">
                  <Label className="text-sm w-44 shrink-0">{OTA_LABELS[ota]}</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    placeholder="15"
                    value={rates[ota] ?? ""}
                    onChange={(e) => setRates((r) => ({ ...r, [ota]: e.target.value }))}
                    className="h-8 w-24"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              ))}
            </div>
            <Button onClick={() => saveRatesMutation.mutate()} disabled={saveRatesMutation.isPending}>
              {saveRatesMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Сохранить ставки
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Hotel list */}
      <Card>
        <CardHeader>
          <CardTitle>Отели</CardTitle>
          <CardDescription>Управление объектами</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {hotels.map((h) => (
            <div key={h.id} className="flex items-center gap-3 rounded-lg border p-3">
              <span className="flex-1 font-medium">{h.name}</span>
              {currentHotel?.id !== h.id && (
                <>
                  <Button variant="outline" size="sm" onClick={() => setCurrentHotelId(h.id)}>
                    Выбрать
                  </Button>
                  <Button
                    variant="ghost" size="icon" className="h-8 w-8 text-red-500"
                    onClick={() => {
                      if (confirm(`Удалить отель "${h.name}" и все его данные?`)) {
                        deleteMutation.mutate(h.id);
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
              {currentHotel?.id === h.id && (
                <span className="text-xs text-muted-foreground px-2">текущий</span>
              )}
            </div>
          ))}

          {!showCreate ? (
            <Button variant="outline" onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Добавить отель
            </Button>
          ) : (
            <div className="flex gap-2">
              <Input
                autoFocus
                placeholder="Название нового отеля"
                value={newHotelName}
                onChange={(e) => setNewHotelName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && newHotelName.trim() && createMutation.mutate()}
              />
              <Button onClick={() => createMutation.mutate()} disabled={!newHotelName.trim() || createMutation.isPending}>
                {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Создать
              </Button>
              <Button variant="outline" onClick={() => { setShowCreate(false); setNewHotelName(""); }}>
                Отмена
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data management */}
      {currentHotel && (
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-red-700">Управление данными</CardTitle>
            <CardDescription>Необратимые действия</CardDescription>
          </CardHeader>
          <CardContent>
            {!confirmClear ? (
              <Button variant="destructive" onClick={() => setConfirmClear(true)}>
                Очистить все данные
              </Button>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-red-700 font-medium">
                  Все бронирования и загрузки будут удалены. Это нельзя отменить.
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    onClick={() => clearMutation.mutate()}
                    disabled={clearMutation.isPending}
                  >
                    {clearMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    Подтвердить удаление
                  </Button>
                  <Button variant="outline" onClick={() => setConfirmClear(false)}>
                    Отмена
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
