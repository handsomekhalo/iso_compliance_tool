import { ShieldCheck } from "lucide-react";

export function AuthShell({ title, subtitle, children }) {
  return (
    <div className="flex min-h-screen flex-col justify-center bg-muted/30 px-6 py-12">
      <div className="mx-auto w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-2 text-lg font-semibold">
          <ShieldCheck className="size-5 text-primary" />
          RandRail
        </div>
        <div className="rounded-lg border border-border bg-background p-6 shadow-sm">
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          {subtitle ? (
            <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          ) : null}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  );
}