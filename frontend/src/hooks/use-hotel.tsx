import React, { createContext, useContext, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { hotels as hotelsApi } from "@/lib/api";
import { keys } from "@/lib/query-client";
import type { Hotel } from "@/types";

interface HotelContextValue {
  currentHotel: Hotel | null;
  setCurrentHotelId: (id: number) => void;
  hotels: Hotel[];
  isLoading: boolean;
}

const HotelContext = createContext<HotelContextValue | null>(null);

export function HotelProvider({ children }: { children: React.ReactNode }) {
  const [currentHotelId, setCurrentHotelId] = useState<number | null>(() => {
    const stored = localStorage.getItem("current_hotel_id");
    return stored ? parseInt(stored, 10) : null;
  });

  const { data: hotelList = [], isLoading } = useQuery({
    queryKey: keys.hotels.all(),
    queryFn: hotelsApi.list,
  });

  // Auto-select first hotel if none selected
  useEffect(() => {
    if (!currentHotelId && hotelList.length > 0) {
      handleSetHotelId(hotelList[0].id);
    }
  }, [hotelList, currentHotelId]);

  const handleSetHotelId = (id: number) => {
    localStorage.setItem("current_hotel_id", String(id));
    setCurrentHotelId(id);
  };

  const currentHotel = hotelList.find((h) => h.id === currentHotelId) ?? null;

  return (
    <HotelContext.Provider
      value={{ currentHotel, setCurrentHotelId: handleSetHotelId, hotels: hotelList, isLoading }}
    >
      {children}
    </HotelContext.Provider>
  );
}

export function useHotel() {
  const ctx = useContext(HotelContext);
  if (!ctx) throw new Error("useHotel must be used within HotelProvider");
  return ctx;
}
