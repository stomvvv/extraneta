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
    detail: (id: string) => ["hotels", id] as const,
    members: (id: string) => ["hotels", id, "members"] as const,
  },
  bookings: {
    list: (hotelId: string, filters?: object) =>
      ["bookings", hotelId, filters] as const,
  },
  analytics: {
    summary: (hotelId: string, params?: object) =>
      ["analytics", "summary", hotelId, params] as const,
    channels: (hotelId: string, params?: object) =>
      ["analytics", "channels", hotelId, params] as const,
    timeSeries: (hotelId: string, params?: object) =>
      ["analytics", "timeSeries", hotelId, params] as const,
    anomalies: (hotelId: string, params?: object) =>
      ["analytics", "anomalies", hotelId, params] as const,
  },
  uploads: {
    list: (hotelId: string) => ["uploads", hotelId] as const,
    detail: (hotelId: string, id: string) => ["uploads", hotelId, id] as const,
  },
  auth: {
    me: () => ["auth", "me"] as const,
  },
};
