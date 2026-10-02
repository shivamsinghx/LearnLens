"use client";

import type { CSSProperties } from "react";

import { DeleteButton } from "@/components/ui/delete-button";

export type StudyDocument = {
  readonly id: string;
  readonly name: string;
  readonly sizeLabel: string;
};

const SERIF_STYLE: CSSProperties = {
  fontFamily:
    'var(--font-serif-display), ui-serif, Georgia, Cambria, "Times New Roman", Times, serif',
};

export function DocumentsSection({
  documents,
  onClearAll,
  cardStyle,
}: {
  documents: readonly StudyDocument[];
  onClearAll?: () => void;
  cardStyle?: CSSProperties;
}) {
  const hasDocuments = documents.length > 0;

  return (
    <section
      id="documents"
      aria-labelledby="documents-heading"
      className="font-sans md:p-8"
      style={cardStyle}
    >
      <h2
        id="documents-heading"
        className="mb-1.5 block w-fit text-lg leading-none text-neutral-900"
        style={SERIF_STYLE}
      >
        Your Documents
      </h2>

      <div className="overflow-hidden rounded-2xl border border-neutral-200/80 bg-white px-5 py-5">
        {hasDocuments ? (
          <ul className="space-y-2">
            {documents.map((document) => (
              <li
                key={document.id}
                className="flex items-center gap-3 rounded-xl border border-neutral-100 bg-neutral-50/80 p-2.5"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-neutral-900">{document.name}</p>
                  <p className="mt-0.5 text-xs text-neutral-500">{document.sizeLabel}</p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="relative flex aspect-[4/3] flex-col items-center justify-center overflow-hidden rounded-xl border border-neutral-100 bg-neutral-50 px-6 text-center">
            <div aria-hidden className="absolute inset-0 grid grid-cols-3 grid-rows-3">
              {Array.from({ length: 9 }, (_, index) => (
                <div key={`docs-grid-${index}`} className="border border-neutral-100/90" />
              ))}
            </div>
            <span
              aria-hidden
              className="absolute top-3 left-3 size-5 border-t-2 border-l-2 border-neutral-300"
            />
            <span
              aria-hidden
              className="absolute top-3 right-3 size-5 border-t-2 border-r-2 border-neutral-300"
            />
            <span
              aria-hidden
              className="absolute bottom-3 left-3 size-5 border-b-2 border-l-2 border-neutral-300"
            />
            <span
              aria-hidden
              className="absolute right-3 bottom-3 size-5 border-r-2 border-b-2 border-neutral-300"
            />

            <div className="relative z-10">
              <p className="text-lg leading-none text-neutral-900" style={SERIF_STYLE}>
                No documents yet
              </p>
              <p className="mt-1 text-sm text-neutral-500">
                Upload your first study document and it will be listed here.
              </p>
            </div>
          </div>
        )}
      </div>

      <p className="mt-1.5 text-xs text-neutral-500">
        {hasDocuments
          ? `${documents.length} file${documents.length === 1 ? "" : "s"} selected locally.`
          : "Selected files stay in this browser until you clear them."}
      </p>

      {hasDocuments && onClearAll ? (
        <div className="mt-4 flex items-center justify-end">
          <DeleteButton onConfirm={onClearAll} />
        </div>
      ) : null}
    </section>
  );
}
