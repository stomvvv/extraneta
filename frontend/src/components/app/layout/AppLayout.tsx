import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard, BookOpen, BarChart3, Upload, FileText,
  Settings, Building2, ChevronDown, Menu, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useHotel } from "@/hooks/use-hotel";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const NAV_ITEMS = [
  { to: "/", icon: LayoutDashboard, label: "Дашборд" },
  { to: "/bookings", icon: BookOpen, label: "Бронирования" },
  { to: "/channels", icon: BarChart3, label: "Каналы" },
  { to: "/upload", icon: Upload, label: "Загрузка" },
  { to: "/reports", icon: FileText, label: "Отчёты" },
  { to: "/settings", icon: Settings, label: "Настройки" },
];

export function AppLayout() {
  const { currentHotel, hotels, setCurrentHotelId } = useHotel();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 w-64 flex flex-col bg-navy-600 text-white transition-transform lg:relative lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Logo */}
        <div className="flex h-14 items-center gap-2 px-6 border-b border-white/10">
          <div className="w-7 h-7 rounded-lg bg-white flex items-center justify-center">
            <span className="text-navy-600 font-black text-sm">E</span>
          </div>
          <span className="font-bold text-lg tracking-tight">ExtranEta</span>
          <button className="ml-auto lg:hidden" onClick={() => setSidebarOpen(false)}>
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Hotel selector */}
        {hotels.length > 0 && (
          <div className="px-4 py-3 border-b border-white/10">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-white/10 transition-colors text-left">
                  <Building2 className="h-4 w-4 shrink-0 text-white/60" />
                  <span className="truncate font-medium">{currentHotel?.name ?? "Выберите отель"}</span>
                  <ChevronDown className="h-3 w-3 ml-auto text-white/60 shrink-0" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56">
                {hotels.map((h) => (
                  <DropdownMenuItem key={h.id} onClick={() => setCurrentHotelId(h.id)}>
                    {h.name}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-white/20 text-white"
                    : "text-white/70 hover:bg-white/10 hover:text-white",
                )
              }
              onClick={() => setSidebarOpen(false)}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="h-14 border-b bg-white flex items-center gap-4 px-4 lg:px-6 shrink-0">
          <button
            className="lg:hidden text-muted-foreground hover:text-foreground"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex-1" />
          {currentHotel && (
            <span className="text-sm text-muted-foreground hidden sm:block">
              {currentHotel.name}
            </span>
          )}
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
