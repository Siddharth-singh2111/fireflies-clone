import { Construction } from "lucide-react";

export function ComingSoon({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <Construction className="h-7 w-7" />
      </div>
      <h1 className="text-xl font-bold">{title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {description ?? "This feature is coming soon. It's a placeholder in this prototype."}
      </p>
    </div>
  );
}
