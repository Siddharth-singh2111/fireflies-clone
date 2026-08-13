"use client";

import Link from "next/link";
import { Bell, Plus } from "lucide-react";
import { useMe } from "@/lib/hooks";
import { Avatar } from "@/components/ui/misc";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { GlobalSearch } from "@/components/GlobalSearch";

export function Topbar({ onNew }: { onNew?: () => void }) {
  const { data: me } = useMe();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur md:px-6">
      <Link href="/" className="flex items-center gap-2 md:hidden">
        <span className="text-base font-semibold">Fireflies</span>
      </Link>

      <div className="flex flex-1 justify-center">
        <GlobalSearch />
      </div>

      <div className="flex items-center gap-1.5">
        {onNew && (
          <Button size="sm" onClick={onNew} className="hidden sm:inline-flex">
            <Plus className="h-4 w-4" /> New meeting
          </Button>
        )}
        <ThemeToggle />
        <Button variant="ghost" size="icon" aria-label="Notifications" className="relative">
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-primary" />
        </Button>
        {me && (
          <Link href="/settings" className="ml-1">
            <Avatar name={me.name} size={34} />
          </Link>
        )}
      </div>
    </header>
  );
}
