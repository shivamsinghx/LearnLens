"use client";

import { useMemo, useRef, useState } from "react";
import {
  FileText,
  Home,
  MoreHorizontal,
  Settings,
  Star,
  Upload,
  X,
} from "lucide-react";

import {
  documentTitle,
  type StudyDocument,
} from "@/app/lib/study-document";
import { SoftUiButton } from "@/components/buttons/soft-ui-button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
} from "@/components/animate-ui/components/radix/sidebar";
import { cn } from "@/lib/cn";

const QUICK_ACTIONS = [
  "Ask a Question",
  "Summarize",
  "Generate Quiz",
  "Study Insights",
] as const;

type NavId = "home" | "documents" | "favorites";

function formatUploadedAt(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function DocumentWorkspace({
  documents,
  activeDocumentId,
  onSelectDocument,
  onAddFiles,
  onGoHome,
}: {
  documents: readonly StudyDocument[];
  activeDocumentId: string | null;
  onSelectDocument: (id: string) => void;
  onAddFiles: (files: File[]) => void;
  onGoHome: () => void;
}) {
  const [nav, setNav] = useState<NavId>("documents");
  const [query, setQuery] = useState("");
  const [recentQuestions, setRecentQuestions] = useState<string[]>([]);
  const [showPdf, setShowPdf] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const active = useMemo(
    () => documents.find((doc) => doc.id === activeDocumentId) ?? documents[0] ?? null,
    [documents, activeDocumentId],
  );

  const title = active ? documentTitle(active.name) : "Documents";

  const submitQuestion = () => {
    const trimmed = query.trim();
    if (!trimmed || !active) return;
    setRecentQuestions((prev) => [trimmed, ...prev].slice(0, 12));
    setQuery("");
  };

  return (
    <SidebarProvider className="bg-[#fbfbfa] text-[#37352f]">
      <Sidebar collapsible="icon" className="border-sidebar-border">
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                size="lg"
                tooltip="LearnLens"
                onClick={onGoHome}
                className="font-semibold tracking-[-0.02em] text-[15px] text-sidebar-foreground"
              >
                <span>
                  Learn
                  <span className="italic">Lens</span>
                </span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>

        <SidebarContent className="overflow-x-hidden">
          <SidebarGroup>
            <SidebarGroupLabel>Workspace</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {(
                  [
                    { id: "home" as const, label: "Home", icon: Home },
                    { id: "documents" as const, label: "Documents", icon: FileText },
                    { id: "favorites" as const, label: "Favorites", icon: Star },
                  ] as const
                ).map((item) => {
                  const Icon = item.icon;
                  return (
                    <SidebarMenuItem key={item.id}>
                      <SidebarMenuButton
                        isActive={nav === item.id}
                        tooltip={item.label}
                        onClick={() => {
                          setNav(item.id);
                          if (item.id === "home") onGoHome();
                        }}
                      >
                        <Icon />
                        <span>{item.label}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          <SidebarSeparator />

          <SidebarGroup>
            <SidebarGroupLabel>Your Documents</SidebarGroupLabel>
            <SidebarGroupAction
              title="Upload PDF"
              aria-label="Upload PDF"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload />
            </SidebarGroupAction>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              multiple
              className="hidden"
              onChange={(event) => {
                const list = event.target.files;
                if (!list?.length) return;
                onAddFiles(Array.from(list));
                event.target.value = "";
              }}
            />
            <SidebarGroupContent>
              <SidebarMenu>
                {documents.map((doc) => (
                  <SidebarMenuItem key={doc.id}>
                    <SidebarMenuButton
                      isActive={active?.id === doc.id}
                      tooltip={doc.name}
                      onClick={() => {
                        onSelectDocument(doc.id);
                        setShowPdf(false);
                      }}
                    >
                      <FileText />
                      <span>{doc.name}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter className="border-t border-sidebar-border">
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton tooltip="Settings" className="gap-2 text-sidebar-foreground">
                <Settings className="size-4 shrink-0" />
                <span>Settings</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>

      <SidebarInset className="bg-[#fbfbfa]">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-black/[0.06] px-3">
          <SidebarTrigger className="-ml-0.5" />
          <div className="h-4 w-px bg-black/[0.08]" aria-hidden />
          <p className="truncate text-[13px] text-[#9b9a97]">
            <span className="text-[#787774]">Documents</span>
            <span className="mx-1.5">/</span>
            <span className="text-[#37352f]">{title}</span>
          </p>
        </header>

        <div className="flex min-h-0 min-w-0 flex-1">
          {showPdf && active ? (
            <section
              aria-label="PDF preview"
              className="flex min-w-0 flex-1 flex-col border-r border-black/[0.06] bg-white"
            >
              <div className="flex items-center justify-between border-b border-black/[0.06] px-4 py-2.5">
                <p className="truncate text-[13px] font-medium text-[#37352f]">{active.name}</p>
                <button
                  type="button"
                  onClick={() => setShowPdf(false)}
                  className="rounded-md p-1 text-[#9b9a97] transition-colors hover:bg-black/[0.04] hover:text-[#37352f]"
                  aria-label="Close PDF"
                >
                  <X className="size-4" strokeWidth={1.75} />
                </button>
              </div>
              <iframe
                title={`Preview of ${active.name}`}
                src={active.objectUrl}
                className="min-h-0 w-full flex-1 bg-neutral-100"
              />
            </section>
          ) : null}

          <div
            id="content"
            className={cn(
              "min-w-0 overflow-y-auto",
              showPdf ? "w-full max-w-xl shrink-0 border-l border-black/[0.04] lg:w-[440px]" : "flex-1",
            )}
          >
            <div
              className={cn(
                "mx-auto w-full px-6 pt-8 pb-16 sm:px-10",
                showPdf ? "max-w-none" : "max-w-3xl px-8 pt-10 pb-20 sm:px-12",
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h1
                    className={cn(
                      "font-bold tracking-[-0.03em] text-[#37352f]",
                      showPdf ? "text-[28px] leading-[1.2]" : "text-[40px] leading-[1.15]",
                    )}
                  >
                    {title}
                  </h1>
                  <p className="mt-2 text-[14px] text-[#787774]">
                    PDF · {active?.sizeLabel ?? "—"} ·{" "}
                    {active?.status === "ready" ? "Analyzed" : "Processing"}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {active ? (
                    <SoftUiButton
                      size="sm"
                      tone="blue"
                      onClick={() => setShowPdf((current) => !current)}
                    >
                      {showPdf ? "Hide PDF" : "View PDF"}
                    </SoftUiButton>
                  ) : null}
                  <button
                    type="button"
                    className="rounded-md p-1.5 text-[#9b9a97] transition-colors hover:bg-black/[0.04] hover:text-[#37352f]"
                    aria-label="Document menu"
                  >
                    <MoreHorizontal className="size-5" strokeWidth={1.75} />
                  </button>
                </div>
              </div>

              <div className="mt-6 border-t border-black/[0.08]" />

              <section className="mt-8" aria-label="Ask about this document">
                <div className="rounded-md border border-black/[0.1] bg-white shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
                  <label htmlFor="doc-ask" className="sr-only">
                    Ask anything about this document
                  </label>
                  <div className="flex items-center gap-2 px-3 py-2.5">
                    <input
                      id="doc-ask"
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          submitQuestion();
                        }
                      }}
                      placeholder="Ask anything about this document..."
                      className="min-w-0 flex-1 bg-transparent text-[15px] text-[#37352f] outline-none placeholder:text-[#9b9a97]"
                    />
                    <button
                      type="button"
                      onClick={submitQuestion}
                      disabled={!query.trim()}
                      className="rounded-md bg-[#37352f] px-3 py-1.5 text-[13px] font-medium text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-35"
                    >
                      Ask
                    </button>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {QUICK_ACTIONS.map((action) => (
                    <button
                      key={action}
                      type="button"
                      onClick={() => setQuery(action)}
                      className="rounded-full border border-black/[0.08] bg-white px-3 py-1 text-[13px] text-[#787774] transition-colors hover:border-black/[0.14] hover:bg-[#f7f7f5] hover:text-[#37352f]"
                    >
                      {action}
                    </button>
                  ))}
                </div>
              </section>

              <section className="mt-12" aria-labelledby="recent-questions-heading">
                <h2
                  id="recent-questions-heading"
                  className="text-[14px] font-semibold text-[#37352f]"
                >
                  Recent questions
                </h2>
                {recentQuestions.length === 0 ? (
                  <p className="mt-3 text-[14px] text-[#9b9a97]">
                    Questions you ask about this document will show up here.
                  </p>
                ) : (
                  <ul className="mt-3 divide-y divide-black/[0.06] border-y border-black/[0.06]">
                    {recentQuestions.map((item) => (
                      <li
                        key={item}
                        className="flex items-start gap-2 py-2.5 text-[14px] text-[#37352f]"
                      >
                        <span className="mt-2 size-1 shrink-0 rounded-full bg-[#9b9a97]" aria-hidden />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              {active ? (
                <section className="mt-12" aria-labelledby="doc-info-heading">
                  <h2 id="doc-info-heading" className="text-[14px] font-semibold text-[#37352f]">
                    Document information
                  </h2>
                  <dl className="mt-3 grid grid-cols-1 gap-3 text-[14px] sm:grid-cols-2">
                    <div className="rounded-md border border-black/[0.06] bg-white px-3 py-2.5">
                      <dt className="text-[12px] text-[#9b9a97]">Filename</dt>
                      <dd className="mt-0.5 truncate font-medium text-[#37352f]">{active.name}</dd>
                    </div>
                    <div className="rounded-md border border-black/[0.06] bg-white px-3 py-2.5">
                      <dt className="text-[12px] text-[#9b9a97]">Size</dt>
                      <dd className="mt-0.5 font-medium text-[#37352f]">{active.sizeLabel}</dd>
                    </div>
                    <div className="rounded-md border border-black/[0.06] bg-white px-3 py-2.5">
                      <dt className="text-[12px] text-[#9b9a97]">Uploaded</dt>
                      <dd className="mt-0.5 font-medium text-[#37352f]">
                        {formatUploadedAt(active.uploadedAt)}
                      </dd>
                    </div>
                    <div className="rounded-md border border-black/[0.06] bg-white px-3 py-2.5">
                      <dt className="text-[12px] text-[#9b9a97]">Status</dt>
                      <dd className="mt-0.5 font-medium text-[#37352f]">
                        {active.status === "ready" ? "Ready" : "Processing"}
                      </dd>
                    </div>
                  </dl>
                </section>
              ) : null}
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
