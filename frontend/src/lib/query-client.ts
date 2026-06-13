import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Query key factories
export const keys = {
  hotels: {
    all: () => ["hotels"] as const,
    detail: (id: number) => ["hotels", id] as const,
  },
  dashboard: {
    data: (hotelId: number | null, params?: object) =>
      ["dashboard", hotelId, params] as const,
  },
  bookings: {
    list: (hotelId: number | null, filters?: object) =>
      ["bookings", hotelId, filters] as const,
  },
  channels: {
    list: (hotelId: number | null, params?: object) =>
      ["channels", hotelId, params] as const,
  },
  uploads: {
    list: (hotelId: number | null) => ["uploads", hotelId] as const,
  },
  settings: {
    commissions: (hotelId: number | null) => ["settings", "commissions", hotelId] as const,
  },
  anomalies: {
    list: (hotelId: number | null, params?: object) =>
      ["anomalies", hotelId, params] as const,
  },
};
