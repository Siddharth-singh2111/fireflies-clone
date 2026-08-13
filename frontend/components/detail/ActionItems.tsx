"use client";

import * as React from "react";
import { Check, Plus, Trash2 } from "lucide-react";
import type { ActionItem } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useActionItemMutations } from "@/lib/hooks";

export function ActionItems({ meetingId, items }: { meetingId: number; items: ActionItem[] }) {
  const { create, update, remove } = useActionItemMutations(meetingId);
  const [text, setText] = React.useState("");
  const [assignee, setAssignee] = React.useState("");

  const add = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    create.mutate(
      { text: text.trim(), assignee: assignee.trim() || null },
      { onSuccess: () => { setText(""); setAssignee(""); } },
    );
  };

  const done = items.filter((i) => i.is_completed).length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {done}/{items.length} completed
        </span>
      </div>

      <ul className="space-y-2">
        {items.map((item) => (
          <li
            key={item.id}
            className="group flex items-start gap-2 rounded-md border border-border p-2.5"
          >
            <button
              onClick={() => update.mutate({ itemId: item.id, body: { is_completed: !item.is_completed } })}
              className={cn(
                "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors",
                item.is_completed
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border hover:border-primary",
              )}
              aria-label={item.is_completed ? "Mark incomplete" : "Mark complete"}
            >
              {item.is_completed && <Check className="h-3.5 w-3.5" />}
            </button>
            <div className="min-w-0 flex-1">
              <p className={cn("text-sm", item.is_completed && "text-muted-foreground line-through")}>
                {item.text}
              </p>
              {item.assignee && (
                <span className="mt-0.5 inline-block rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                  @{item.assignee}
                </span>
              )}
            </div>
            <button
              onClick={() => remove.mutate(item.id)}
              className="rounded p-1 text-muted-foreground opacity-0 hover:bg-muted hover:text-red-600 group-hover:opacity-100"
              aria-label="Delete action item"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </li>
        ))}
        {items.length === 0 && (
          <li className="rounded-md border border-dashed border-border p-4 text-center text-sm text-muted-foreground">
            No action items yet.
          </li>
        )}
      </ul>

      <form onSubmit={add} className="space-y-2 rounded-md border border-border p-2.5">
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Add an action item…"
          className="h-9"
        />
        <div className="flex gap-2">
          <Input
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
            placeholder="Assignee (optional)"
            className="h-9"
          />
          <Button type="submit" size="sm" disabled={!text.trim() || create.isPending}>
            <Plus className="h-4 w-4" /> Add
          </Button>
        </div>
      </form>
    </div>
  );
}
