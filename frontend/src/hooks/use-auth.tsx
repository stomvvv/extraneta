import React, { createContext, useContext } from "react";
import type { User } from "@/types";

const DEMO_USER: User = {
  id: "00000000-0000-0000-0000-000000000001",
  email: "demo@extraneta.ru",
  full_name: "Demo User",
  is_active: true,
  is_verified: true,
};

interface AuthContextValue {
  user: User;
}

const AuthContext = createContext<AuthContextValue>({ user: DEMO_USER });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <AuthContext.Provider value={{ user: DEMO_USER }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
