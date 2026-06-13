import type {
  Hotel, Booking, BookingListResponse, DashboardData,
  ChannelMetrics, Upload, CommissionSetting,
} from "@/types";

const BASE_URL = "/api";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new ApiError(resp.status, body.detail || "Request failed");
  }

  if (resp.status === 204) return undefined as T;
  return resp.json();
}

function toQuery(params: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) {
      v.forEach((i) => parts.push(`${k}=${encodeURIComponent(String(i))}`));
    } else {
      parts.push(`${k}=${encodeURIComponent(String(v))}`);
    }
  }
  return parts.length ? `?${parts.join("&")}` : "";
}

// Hotels
export const hotels = {
  list: () => request<Hotel[]>("/hotels"),
  create: (data: { name: string; address?: string }) =>
    request<Hotel>("/hotels", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: { name?: string; address?: string }) =>
    request<Hotel>(`/hotels/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<void>(`/hotels/${id}`, { method: "DELETE" }),
};

// Dashboard
export interface DashboardParams {
  hotel_id?: number;
  period?: string;
  date_from?: string;
  date_to?: string;
}

export const dashboard = {
  get: (params: DashboardParams = {}) =>
    request<DashboardData>(`/dashboard${toQuery(params as Record<string, unknown>)}`),
};

// Bookings
export interface BookingFilters {
  hotel_id?: number;
  page?: number;
  limit?: number;
  ota?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  is_anomaly?: boolean;
  guest?: string;
}

export const bookings = {
  list: (filters: BookingFilters = {}) =>
    request<BookingListResponse>(`/bookings${toQuery(filters as Record<string, unknown>)}`),
  exportUrl: (filters: BookingFilters = {}) =>
    `${BASE_URL}/bookings/export${toQuery(filters as Record<string, unknown>)}`,
};

// Channels
export interface ChannelsParams {
  hotel_id?: number;
  period?: string;
  date_from?: string;
  date_to?: string;
}

export const channels = {
  list: (params: ChannelsParams = {}) =>
    request<ChannelMetrics[]>(`/channels${toQuery(params as Record<string, unknown>)}`),
};

// Uploads
export const uploads = {
  list: (hotel_id?: number) =>
    request<Upload[]>(`/uploads${hotel_id ? `?hotel_id=${hotel_id}` : ""}`),
  upload: (file: File, ota: string, hotel_id?: number) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("ota", ota);
    if (hotel_id) fd.append("hotel_id", String(hotel_id));
    return request<Upload>("/upload", { method: "POST", body: fd });
  },
  delete: (id: number) =>
    request<void>(`/uploads/${id}`, { method: "DELETE" }),
};

// Reports
export const reports = {
  excelUrl: (params: { hotel_id?: number; date_from?: string; date_to?: string }) =>
    `${BASE_URL}/reports/excel${toQuery(params as Record<string, unknown>)}`,
  pdfUrl: (params: { hotel_id?: number; date_from?: string; date_to?: string }) =>
    `${BASE_URL}/reports/pdf${toQuery(params as Record<string, unknown>)}`,
};

// Settings
export const settings = {
  getCommissions: (hotel_id?: number) =>
    request<CommissionSetting[]>(`/settings/commissions${hotel_id ? `?hotel_id=${hotel_id}` : ""}`),
  updateCommissions: (updates: { ota: string; expected_rate: number }[], hotel_id?: number) =>
    request<{ ok: boolean }>(`/settings/commissions${hotel_id ? `?hotel_id=${hotel_id}` : ""}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    }),
  clearData: (hotel_id?: number) =>
    request<void>(`/settings/data${hotel_id ? `?hotel_id=${hotel_id}` : ""}`, { method: "DELETE" }),
};
