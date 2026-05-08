"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  color?: "blue" | "violet" | "green" | "orange" | "red";
  delay?: number;
}

const colorMap = {
  blue: "from-blue-500/20 to-blue-600/5 text-blue-600 dark:text-blue-400",
  violet: "from-violet-500/20 to-violet-600/5 text-violet-600 dark:text-violet-400",
  green: "from-green-500/20 to-green-600/5 text-green-600 dark:text-green-400",
  orange: "from-orange-500/20 to-orange-600/5 text-orange-600 dark:text-orange-400",
  red: "from-red-500/20 to-red-600/5 text-red-600 dark:text-red-400",
};

export function StatCard({ title, value, subtitle, icon: Icon, trend, color = "blue", delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
    >
      <Card className="overflow-hidden">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{title}</p>
              <p className="text-2xl font-bold mt-1 truncate">{value}</p>
              {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
              {trend && (
                <p className={cn("text-xs mt-1 font-medium", trend.value >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600")}>
                  {trend.value >= 0 ? "↑" : "↓"} {Math.abs(trend.value)}% {trend.label}
                </p>
              )}
            </div>
            <div className={cn("w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center flex-shrink-0 ml-3", colorMap[color])}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
