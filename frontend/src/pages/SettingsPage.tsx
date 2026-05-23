import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Loader2, Trash2, UserPlus, Building2 } from "lucide-react";

import { hotels } from "@/lib/api";
import { keys } from "@/lib/query-client";
import { useHotel } from "@/hooks/use-hotel";
import { toast } from "@/hooks/use-toast";
import { OTA_LABELS } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import type { Hotel, UserRole } from "@/types";

const OTA_KEYS = ["yandex", "ostrovok", "bronevoy", "tinkoff", "2gis", "hotel101", "academservis"] as const;

export default function SettingsPage() {
  const { currentHotel, setCurrentHotelId } = useHotel();
  const qc = useQueryClient();

  // Hotel form
  const [hotelForm, setHotelForm] = useState<Partial<Hotel>>({});
  const [rates, setRates] = useState<Record<string, string>>({});
  const [loadedHotelId, setLoadedHotelId] = useState<string | null>(null);
  const [newHotelName, setNewHotelName] = useState("");
  const [showCreateHotel, setShowCreateHotel] = useState(false);

  // Invite form
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<UserRole>("manager");
  const [inviteLink, setInviteLink] = useState<string | null>(null);

  // Load hotel data when hotel changes
  if (currentHotel && currentHotel.id !== loadedHotelId) {
    setLoadedHotelId(currentHotel.id);
    setHotelForm({ name: currentHotel.name, room_count: currentHotel.room_count ?? undefined });
    const r: Record<string, string> = {};
    OTA_KEYS.forEach((k) => {
      r[k] = String(currentHotel.expected_commission_rates[k] ?? "");
    });
    setRates(r);
  }

  const { data: members = [] } = useQuery({
    queryKey: keys.hotels.members(currentHotel?.id ?? ""),
    queryFn: () => hotels.members(currentHotel!.id),
    enabled: !!currentHotel,
  });

  const updateHotelMutation = useMutation({
    mutationFn: (data: Partial<Hotel>) => hotels.update(currentHotel!.id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.hotels.all() });
      toast({ title: "Настройки сохранены", variant: "success" });
    },
    onError: (e: any) => toast({ title: "Ошибка", description: e.message, variant: "destructive" }),
  });

  const createHotelMutation = useMutation({
    mutationFn: (name: string) => hotels.create({ name }),
    onSuccess: (h) => {
      qc.invalidateQueries({ queryKey: keys.hotels.all() });
      setCurrentHotelId(h.id);
      setShowCreateHotel(false);
      setNewHotelName("");
      toast({ title: `Отель "${h.name}" создан`, variant: "success" });
    },
    onError: (e: any) => toast({ title: "Ошибка создания отеля", description: e.message, variant: "destructive" }),
  });

  const inviteMutation = useMutation({
    mutationFn: () => hotels.invite(currentHotel!.id, inviteEmail, inviteRole),
    onSuccess: (data) => {
      setInviteLink(data.invite_url);
      setInviteEmail("");
    },
    onError: (e: any) => toast({ title: "Ошибка", description: e.message, variant: "destructive" }),
  });

  const handleSaveHotel = () => {
    const commissionRates: Record<string, number> = {};
    OTA_KEYS.forEach((k) => {
      const val = parseFloat(rates[k]);
      if (!isNaN(val)) commissionRates[k] = val;
    });
    updateHotelMutation.mutate({
      name: hotelForm.name,
      room_count: hotelForm.room_count,
      expected_commission_rates: commissionRates,
    });
  };

  const roleLabels: Record<UserRole, string> = {
    owner: "Владелец",
    manager: "Менеджер",
    accountant: "Бухгалтер",
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold">Настройки</h1>

      {/* Hotel settings */}
      {currentHotel && (
        <Card>
          <CardHeader>
            <CardTitle>Параметры отеля</CardTitle>
            <CardDescription>Основная информация и ожидаемые ставки комиссий</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Название отеля</Label>
                <Input
                  id="name"
                  value={hotelForm.name ?? ""}
                  onChange={(e) => setHotelForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="room_count">Количество номеров</Label>
                <Input
                  id="room_count"
                  type="number"
                  min={1}
                  placeholder="Для расчёта загрузки"
                  value={hotelForm.room_count ?? ""}
                  onChange={(e) => setHotelForm((f) => ({
                    ...f,
                    room_count: e.target.value ? parseInt(e.target.value) : undefined,
                  }))}
                />
              </div>
            </div>

            <Separator />

            <div>
              <Label className="text-sm font-semibold">Ожидаемые ставки комиссий (%)</Label>
              <p className="text-xs text-muted-foreground mt-1 mb-3">
                Используются для выявления аномалий. Отклонение &gt;1% считается аномалией.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {OTA_KEYS.map((ota) => (
                  <div key={ota} className="flex items-center gap-2">
                    <span className="text-sm w-40 shrink-0">{OTA_LABELS[ota]}</span>
                    <Input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      placeholder="напр. 15"
                      value={rates[ota] ?? ""}
                      onChange={(e) => setRates((r) => ({ ...r, [ota]: e.target.value }))}
                      className="h-8"
                    />
                    <span className="text-sm text-muted-foreground">%</span>
                  </div>
                ))}
              </div>
            </div>

            <Button onClick={handleSaveHotel} disabled={updateHotelMutation.isPending}>
              {updateHotelMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Сохранить
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Create new hotel */}
      <Card>
        <CardHeader>
          <CardTitle>Добавить отель</CardTitle>
          <CardDescription>Один аккаунт может управлять несколькими объектами</CardDescription>
        </CardHeader>
        <CardContent>
          {!showCreateHotel ? (
            <Button variant="outline" onClick={() => setShowCreateHotel(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Добавить отель
            </Button>
          ) : (
            <div className="flex gap-3">
              <Input
                placeholder="Название отеля"
                value={newHotelName}
                onChange={(e) => setNewHotelName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && createHotelMutation.mutate(newHotelName)}
              />
              <Button
                onClick={() => createHotelMutation.mutate(newHotelName)}
                disabled={!newHotelName.trim() || createHotelMutation.isPending}
              >
                {createHotelMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Создать
              </Button>
              <Button variant="outline" onClick={() => { setShowCreateHotel(false); setNewHotelName(""); }}>
                Отмена
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Team members */}
      {currentHotel && (
        <Card>
          <CardHeader>
            <CardTitle>Команда</CardTitle>
            <CardDescription>Управление доступом к {currentHotel.name}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Member list */}
            <div className="space-y-2">
              {members.map((m) => (
                <div key={m.id} className="flex items-center gap-3 rounded-lg border p-3">
                  <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold">
                      {(m.user_full_name || m.user_email || "?")[0].toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{m.user_full_name || m.user_email}</p>
                    <p className="text-xs text-muted-foreground truncate">{m.user_email}</p>
                  </div>
                  <Badge variant={m.role === "owner" ? "default" : "secondary"}>
                    {roleLabels[m.role]}
                  </Badge>
                </div>
              ))}
            </div>

            <Separator />

            {/* Invite */}
            <div className="space-y-3">
              <Label className="font-semibold">Пригласить участника</Label>
              <div className="flex flex-wrap gap-2">
                <Input
                  type="email"
                  placeholder="email@example.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="flex-1 min-w-48"
                />
                <Select value={inviteRole} onValueChange={(v) => setInviteRole(v as UserRole)}>
                  <SelectTrigger className="w-36">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="manager">Менеджер</SelectItem>
                    <SelectItem value="accountant">Бухгалтер</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  onClick={() => inviteMutation.mutate()}
                  disabled={!inviteEmail.trim() || inviteMutation.isPending}
                >
                  {inviteMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  <UserPlus className="h-4 w-4 mr-1.5" />
                  Пригласить
                </Button>
              </div>
              {inviteLink && (
                <div className="rounded-lg bg-muted p-3 text-sm">
                  <p className="font-medium mb-1">Ссылка для приглашения:</p>
                  <p className="break-all text-muted-foreground font-mono text-xs">{inviteLink}</p>
                  <Button variant="outline" size="sm" className="mt-2 h-7" onClick={() => {
                    navigator.clipboard.writeText(inviteLink);
                    toast({ title: "Скопировано", variant: "success" });
                  }}>
                    Скопировать
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
