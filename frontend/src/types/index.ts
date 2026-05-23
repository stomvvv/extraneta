export type OTASource =
  | "yandex"
  | "ostrovok"
  | "bronevoy"
  | "tinkoff"
  | "2gis"
  | "hotel101"
  | "academservis";

export type PaymentStatus = "paid" | "pending" | "cancelled" | "refunded";
export type BookingStatus = "confirmed" | "cancelled" | "no_show";
export type UserRole = "owner" | "manager" | "accountant";
export type UploadStatus = "pending" | "processing" | "completed" | "failed";
export type DocumentType = "booking_report" | "financial_report" | "reconciliation_act";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface Hotel {
  id: string;
  name: string;
  room_count: number | null;
  expected_commission_rates: Record<string, number>;
  currency: string;
  timezone: string;
}

export interface HotelMember {
  id: string;
  user_id: string;
  hotel_id: string;
  role: UserRole;
  user_email?: string;
  user_full_name?: string;
}

export interface Booking {
  id: string;
  hotel_id: string;
  upload_id: string | null;
  source_ota: OTASource;
  booking_id_ota: string;
  guest_name: string;
  room_type: string | null;
  booking_date: string | null;
  check_in: string;
  check_out: string;
  nights: number;
  gross_amount: string;
  ota_commission_rate: string;
  ota_commission_amount: string;
  net_amount: string;
  currency: string;
  payment_status: PaymentStatus;
  booking_status: BookingStatus;
  has_vat: boolean;
  is_anomaly: boolean;
  anomaly_reasons: string | null;
  created_at: string;
}

export interface BookingListResponse {
  items: Booking[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SummaryMetrics {
  gross_revenue: string;
  total_commission: string;
  net_revenue: string;
  commission_rate_pct: string;
  total_bookings: number;
  confirmed_bookings: number;
  cancelled_bookings: number;
  avg_booking_value: string;
  occupancy_pct: string | null;
  period_start: string;
  period_end: string;
  gross_revenue_change_pct: string | null;
  net_revenue_change_pct: string | null;
  bookings_change_pct: string | null;
}

export interface ChannelMetrics {
  source_ota: string;
  bookings_count: number;
  gross_revenue: string;
  commission_amount: string;
  commission_rate_pct: string;
  net_revenue: string;
  channel_share_pct: string;
  avg_booking_value: string;
}

export interface TimeSeriesPoint {
  period: string;
  gross_revenue: string;
  commission_amount: string;
  net_revenue: string;
  bookings_count: number;
}

export interface AnomalySummary {
  total_anomalies: number;
  commission_rate_deviations: number;
  duplicate_bookings: number;
  invalid_commissions: number;
  cancelled_unreturned: number;
  affected_revenue: string;
}

export interface Upload {
  id: string;
  hotel_id: string;
  original_filename: string;
  file_size_bytes: number;
  source_ota: OTASource;
  document_type: DocumentType;
  status: UploadStatus;
  bookings_imported: number;
  bookings_skipped: number;
  error_message: string | null;
  report_period_start: string | null;
  report_period_end: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface DateRange {
  from: Date;
  to: Date;
}
