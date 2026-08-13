"use client";

import { Bell, Palette, Puzzle, Shield, User } from "lucide-react";
import { useMe } from "@/lib/hooks";
import { Avatar } from "@/components/ui/misc";
import { ThemeToggle } from "@/components/ThemeToggle";

const PLACEHOLDERS = [
  { icon: Bell, title: "Notifications", desc: "Email and in-app alerts for new summaries." },
  { icon: Puzzle, title: "Integrations", desc: "Zoom, Google Meet, Slack, and calendar sync." },
  { icon: Shield, title: "Security & Privacy", desc: "Data retention and access controls." },
];

export default function SettingsPage() {
  const { data: me } = useMe();

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 md:px-6">
      <h1 className="mb-6 text-2xl font-bold tracking-tight">Settings</h1>

      {/* Profile */}
      <section className="mb-6 rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <User className="h-4 w-4 text-primary" />
          <h2 className="font-semibold">Profile</h2>
        </div>
        {me && (
          <div className="flex items-center gap-4">
            <Avatar name={me.name} size={56} />
            <div>
              <p className="font-medium">{me.name}</p>
              <p className="text-sm text-muted-foreground">{me.email}</p>
              <span className="mt-1 inline-block rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                Default user (authentication is mocked in this prototype)
              </span>
            </div>
          </div>
        )}
      </section>

      {/* Appearance */}
      <section className="mb-6 rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Palette className="h-4 w-4 text-primary" />
          <h2 className="font-semibold">Appearance</h2>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Theme</p>
            <p className="text-sm text-muted-foreground">Switch between light and dark mode.</p>
          </div>
          <ThemeToggle />
        </div>
      </section>

      {/* Placeholder sections */}
      <section className="space-y-3">
        {PLACEHOLDERS.map((p) => {
          const Icon = p.icon;
          return (
            <div
              key={p.title}
              className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium">{p.title}</p>
                  <p className="text-sm text-muted-foreground">{p.desc}</p>
                </div>
              </div>
              <span className="rounded bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">
                Coming soon
              </span>
            </div>
          );
        })}
      </section>
    </div>
  );
}
