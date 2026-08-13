"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CalendarClock,
  Home,
  Puzzle,
  Settings,
  Sparkles,
  Star,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Home", icon: Home },
  { href: "/?filter=starred", label: "Starred", icon: Star, soon: true },
  { href: "/?filter=upcoming", label: "Upcoming", icon: CalendarClock, soon: true },
  { href: "/team", label: "Team", icon: Users, soon: true },
  { href: "/integrations", label: "Integrations", icon: Puzzle, soon: true },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-60 shrink-0 flex-col bg-sidebar text-white/90 md:flex">
      <div className="flex h-16 items-center gap-2 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
          <Sparkles className="h-5 w-5 text-white" />
        </div>
        <span className="text-lg font-semibold tracking-tight">Fireflies</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-white/15 text-white" : "text-white/70 hover:bg-white/10 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
              {item.soon && (
                <span className="ml-auto rounded bg-white/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-white/50">
                  Soon
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-4 text-xs text-white/50">
        <p className="font-medium text-white/70">Fireflies Clone</p>
        <p>Meeting notes & transcripts</p>
      </div>
    </aside>
  );
}
