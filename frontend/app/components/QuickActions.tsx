"use client";

import { useMemo, useState } from "react";

import AnimatedTabs from "@/components/forgeui/animated-tabs";

const TAB_CONTENT = [
  {
    title: "Ask a Question",
    description: "Ask about a passage in your uploaded material.",
  },
  {
    title: "Summarize",
    description: "Turn a document into a short summary.",
  },
  {
    title: "Generate Quiz",
    description: "Practice with questions drawn from your material.",
  },
  {
    title: "Study Insights",
    description: "See which parts of a document need more review.",
  },
] as const;

const TABS = TAB_CONTENT.map((tab) => tab.title);

export function QuickActions() {
  const [activeTab, setActiveTab] = useState<string>(TABS[0]);
  const active = useMemo(
    () => TAB_CONTENT.find((tab) => tab.title === activeTab) ?? TAB_CONTENT[0],
    [activeTab],
  );

  return (
    <section id="actions" aria-labelledby="actions-heading">
      <div className="max-w-2xl">
        <h2 id="actions-heading" className="text-2xl font-semibold tracking-[-0.03em] text-black/95">
          Quick Actions
        </h2>
        <p id="actions-availability" className="mt-2 text-sm leading-6 text-muted">
          Available after uploading a document.
        </p>
      </div>

      <div className="mt-8 flex flex-col items-center gap-8">
        <AnimatedTabs
          tabs={[...TABS]}
          variant="default"
          value={activeTab}
          onValueChange={setActiveTab}
        />

        <div
          aria-describedby="actions-availability"
          className="w-full max-w-3xl rounded-3xl border border-black/8 bg-neutral-50 px-6 py-8 text-center sm:px-10 sm:py-10"
        >
          <p className="text-xl font-semibold tracking-[-0.02em] text-black sm:text-2xl">
            {active.title}
          </p>
          <p className="mx-auto mt-3 max-w-xl text-base leading-7 text-black/70 sm:text-lg sm:leading-8">
            {active.description}
          </p>
          <p className="mt-8 text-xs font-medium tracking-wide text-black/45 uppercase sm:text-sm">
            Available after uploading a document
          </p>
        </div>
      </div>
    </section>
  );
}
