"use client";

import * as React from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CreateMeetingModal } from "@/components/meetings/CreateMeetingModal";

/** Lets any page open the global "new meeting" modal via useCreateMeetingModal(). */
const CreateModalContext = React.createContext<() => void>(() => {});
export const useCreateMeetingModal = () => React.useContext(CreateModalContext);

/**
 * Client shell wrapping every page: the dark sidebar rail, the sticky topbar
 * (global search + theme + new-meeting), and a globally-available "create
 * meeting" modal so the action works from anywhere in the app.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [createOpen, setCreateOpen] = React.useState(false);
  const open = React.useCallback(() => setCreateOpen(true), []);

  return (
    <CreateModalContext.Provider value={open}>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Topbar onNew={open} />
          <main className="flex-1 overflow-y-auto scroll-thin">{children}</main>
        </div>
        <CreateMeetingModal open={createOpen} onClose={() => setCreateOpen(false)} />
      </div>
    </CreateModalContext.Provider>
  );
}
