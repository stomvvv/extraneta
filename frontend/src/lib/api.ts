import type {
  Hotel, HotelMember, Booking, BookingListResponse,
  SummaryMetrics, ChannelMetrics, TimeSeriesPoint, AnomalySummary, Upload,
  OTASource, DocumentType, UserRole,
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

// ── Hotels ────────────────────────────────────────────────────────────────────

export const hotels = {
  list: () => request<Hotel[]>("/hotels"),
  get: (id: string) => request<Hotel>(`/hotels/${id}`),
  create: (data: Partial<Hotel>) =>
    request<Hotel>("/hotels", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<Hotel>) =>
    request<Hotel>(`/hotels/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) =>
    request<void>(`/hotels/${id}`, { method: "DELETE" }),

  members: (id: string) => request<HotelMember[]>(`/hotels/${id}/members`),
  invite: (id: string, email: string, role: UserRole) =>
    request<{ invite_url: string; token: string }>(
      `/hotels/${id}/invite`,
      { method: "POST", body: JSON.stringify({ email, role }) },
    ),
};

// ── Bookings ──────────────────────────────────────────────────────────────────

export interface BookingFilters {
  source_ota?: string[];
  payment_status?: string[];
  booking_status?: string[];
  check_in_from?: string;
  check_in_to?: string;
  guest_name?: string;
  booking_id_ota?: string;
  is_anomaly?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_desc?: boolean;
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

export const bookings = {
  list: (hotelId: string, filters: BookingFilters = {}) =>
    request<BookingListResponse>(`/hotels/${hotelId}/bookings${toQuery(filters as Record<string, unknown>)}`),
};

// ── Analytics ────────────────────────────────────────────────────────────────

export interface AnalyticsParams {
  date_from?: string;
  date_to?: string;
  compare_from?: string;
  compare_to?: string;
  granularity?: "month" | "week";
}

export const analytics = {
  summary: (hotelId: string, params: AnalyticsParams = {}) =>
    request<SummaryMetrics>(`/hotels/${hotelId}/analytics/summary${toQuery(params)}`),
  channels: (hotelId: string, params: AnalyticsParams = {}) =>
    request<ChannelMetrics[]>(`/hotels/${hotelId}/analytics/channels${toQuery(params)}`),
  timeSeries: (hotelId: string, params: AnalyticsParams = {}) =>
    request<TimeSeriesPoint[]>(`/hotels/${hotelId}/analytics/time-series${toQuery(params)}`),
  anomalies: (hotelId: string, params: AnalyticsParams = {}) =>
    request<AnomalySummary>(`/hotels/${hotelId}/analytics/anomalies${toQuery(params)}`),
};

// ── Uploads ───────────────────────────────────────────────────────────────────

export const uploads = {
  list: (hotelId: string) => request<Upload[]>(`/hotels/${hotelId}/uploads`),
  get: (hotelId: string, uploadId: string) =>
    request<Upload>(`/hotels/${hotelId}/uploads/${uploadId}`),

  create: (
    hotelId: string,
    file: File,
    source_ota: OTASource,
    document_type: DocumentType,
    period_start?: string,
    period_end?: string,
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("source_ota", source_ota);
    fd.append("document_type", document_type);
    if (period_start) fd.append("report_period_start", period_start);
    if (period_end) fd.append("report_period_end", period_end);
    return request<Upload>(`/hotels/${hotelId}/uploads`, { method: "POST", body: fd });
  },

  delete: (hotelId: string, uploadId: string) =>
    request<void>(`/hotels/${hotelId}/uploads/${uploadId}`, { method: "DELETE" }),

  reimport: (hotelId: string, uploadId: string) =>
    request<Upload>(`/hotels/${hotelId}/uploads/${uploadId}/reimport`, { method: "POST" }),
};

// ── Reports ───────────────────────────────────────────────────────────────────

export const reports = {
  excelUrl: (hotelId: string, dateFrom: string, dateTo: string) =>
    `/api/hotels/${hotelId}/reports/excel?date_from=${dateFrom}&date_to=${dateTo}`,
  pdfUrl: (hotelId: string, dateFrom: string, dateTo: string) =>
    `/api/hotels/${hotelId}/reports/pdf?date_from=${dateFrom}&date_to=${dateTo}`,
};
