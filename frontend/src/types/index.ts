export type OTASource =
  | "yandex"
  | "ostrovok"
  | "bronevic"
  | "tinkoff"
  | "2gis"
  | "101hotel"
  | "academservis";

export type BookingStatus = "confirmed" | "cancelled" | "no_show";
export type UploadStatus = "processing" | "done" | "error";

export interface Hotel {
  id: number;
  name: string;
  address: string;
}

export interface Booking {
  id: number;
  hotel_id: number;
  upload_id: number | null;
  source_ota: string;
  booking_id_ota: string;
  guest_name: string;
  room_type: string;
  check_in: string;
  check_out: string;
  nights: number;
  gross_amount: number;
  ota_commission_rate: number;
  ota_commission_amount: number;
  net_amount: number;
  currency: string;
  payment_status: string;
  booking_status: BookingStatus;
  has_anomaly: boolean;
  anomaly_reason: string;
  created_at: string;
}

export interface BookingListResponse {
  items: Booking[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface KpiMetrics {
  gross_revenue: number;
  total_commission: number;
  net_revenue: number;
  commission_rate_pct: number;
  total_bookings: number;
  confirmed_bookings: number;
  cancelled_bookings: number;
  avg_booking_value: number;
  anomaly_count: number;
}

export interface TimeSeriesPoint {
  period: string;
  gross_revenue: number;
  commission_amount: number;
  net_revenue: number;
  bookings: number;
}

export interface ChannelMetrics {
  source_ota: string;
  ota_name: string;
  bookings: number;
  gross_revenue: number;
  commission_amount: number;
  net_revenue: number;
  real_commission_rate: number;
  expected_commission_rate: number;
  deviation: number;
  status: "ok" | "warning";
  share_pct: number;
}

export interface DashboardData {
  kpi: KpiMetrics;
  time_series: TimeSeriesPoint[];
  channels: ChannelMetrics[];
  period: { date_from: string; date_to: string };
}

export interface Upload {
  id: number;
  hotel_id: number;
  filename: string;
  ota: string;
  status: UploadStatus;
  records_total: number;
  records_added: number;
  records_skipped: number;
  error_message: string;
  uploaded_at: string;
}

export interface CommissionSetting {
  id: number;
  ota: string;
  expected_rate: number;
}

export interface DateRange {
  from: Date;
  to: Date;
}
