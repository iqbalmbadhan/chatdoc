"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard, FileText, Cpu, Key, BarChart2, Users,
  MessageSquare, ScrollText, Settings, Activity, Bot, LogOut, ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/admin/documents", label: "Documents", icon: FileText },
  { href: "/admin/models", label: "AI Models", icon: Cpu },
  { href: "/admin/keys", label: "API Keys", icon: Key },
  { href: "/admin/analytics", label: "Usage Analytics", icon: BarChart2 },
  { href: "/admin/visitors", label: "Visitor Analytics", icon: Users },
  { href: "/admin/chats", label: "Chats", icon: MessageSquare },
  { href: "/admin/logs", label: "Logs", icon: ScrollText },
  { href: "/admin/settings", label: "Settings", icon: Settings },
  { href: "/admin/system", label: "System Health", icon: Activity },
];

export function AdminSidebar({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="flex flex-col h-full bg-sidebar border-r">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="font-bold text-sm text-sidebar-foreground">ChatDoc</p>
          <p className="text-xs text-muted-foreground">Admin</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <Link key={item.href} href={item.href} onClick={onClose}>
              <motion.div
                whileTap={{ scale: 0.97 }}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all group",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                <span className="flex-1">{item.label}</span>
                {isActive && <ChevronRight className="w-3 h-3 opacity-60" />}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="border-t px-3 py-3">
        <div className="flex items-center gap-2.5 mb-2 px-1">
          <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold">
            {user?.email?.[0]?.toUpperCase() || "A"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium truncate">{user?.email}</p>
            <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
          </div>
        </div>
        <Link href="/chat">
          <Button variant="ghost" size="sm" className="w-full justify-start gap-2 text-xs mb-1">
            <MessageSquare className="w-3.5 h-3.5" /> Open Chat
          </Button>
        </Link>
        <Button variant="ghost" size="sm" onClick={handleLogout} className="w-full justify-start gap-2 text-xs text-destructive hover:text-destructive">
          <LogOut className="w-3.5 h-3.5" /> Sign Out
        </Button>
      </div>
    </div>
  );
}
