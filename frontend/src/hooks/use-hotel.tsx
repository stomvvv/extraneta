import React, { createContext, useContext, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { hotels } from "@/lib/api";
import { keys } from "@/lib/query-client";
import type { Hotel } from "@/types";

interface HotelContextValue {
  currentHotel: Hotel | null;
  setCurrentHotelId: (id: string) => void;
  hotels: Hotel[];
  isLoading: boolean;
}

const HotelContext = createContext<HotelContextValue | null>(null);

export function HotelProvider({ children }: { children: React.ReactNode }) {
  const [currentHotelId, setCurrentHotelId] = useState<string | null>(
    () => localStorage.getItem("current_hotel_id"),
  );

  const { data: hotelList = [], isLoading } = useQuery({
    queryKey: keys.hotels.all(),
    queryFn: hotels.list,
  });

  // Auto-select first hotel if none selected
  useEffect(() => {
    if (!currentHotelId && hotelList.length > 0) {
      setCurrentHotelId(hotelList[0].id);
    }
  }, [hotelList, currentHotelId]);

  const handleSetHotelId = (id: string) => {
    localStorage.setItem("current_hotel_id", id);
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
