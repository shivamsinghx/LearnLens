"use client";

import { useState, type CSSProperties } from "react";

import type { StudyDocument } from "@/app/lib/study-document";
import { FileUploadFieldInput } from "@/components/inputs/file-upload-field-input";
import { WavyDotGrid } from "@/components/ui/wavy-dot-grid";

import { DocumentsSection } from "./DocumentsSection";

/** Soft UI / neumorphic — same dual-shadow language as SoftUiButton. */
const SOFT_CARD_STYLE: CSSProperties = {
  borderRadius: "1.5rem",
  border: "none",
  background: "#f5f5f5",
  padding: "1.75rem",
  boxShadow: "10px 10px 20px #d1d1d1, -10px -10px 20px #ffffff",
  position: "relative",
  zIndex: 1,
};

const SOFT_SURFACE_STYLE: CSSProperties = {
  position: "relative",
  borderRadius: "2rem",
  background: "#f5f5f5",
  padding: "1.75rem",
};

export function StudyMaterials({
  documents,
  processingLabel = null,
  onFilesChange,
  onProceed,
  onClearAll,
  onOpenDocument,
}: {
  documents: readonly StudyDocument[];
  processingLabel?: string | null;
  onFilesChange: (files: File[]) => void;
  onProceed: () => void;
  onClearAll: () => void;
  onOpenDocument?: (id: string) => void;
}) {
  const [uploadKey, setUploadKey] = useState(0);
  const [pendingCount, setPendingCount] = useState(0);
  const isProcessing = Boolean(processingLabel);

  const clearAllDocuments = () => {
    onClearAll();
    setPendingCount(0);
    setUploadKey((current) => current + 1);
  };

  return (
    <div style={SOFT_SURFACE_STYLE}>
      <WavyDotGrid />
      <div
        className="relative z-10 grid grid-cols-1 items-start lg:grid-cols-2"
        style={{ gap: "3.25rem" }}
      >
        <section
          id="upload"
          aria-label="Upload study material"
          className="relative font-sans md:p-8"
          style={SOFT_CARD_STYLE}
          aria-busy={isProcessing || undefined}
        >
          <FileUploadFieldInput
            key={uploadKey}
            label="Upload study material"
            browseLabel="Browse files"
            dropLabel="Drop your files here"
            hint="PDF files supported."
            accept=".pdf"
            multiple
            maxFiles={5}
            maxSizeBytes={10 * 1024 * 1024}
            containerClassName="max-w-none"
            disabled={isProcessing}
            proceedLabel="Proceed"
            proceedDisabled={pendingCount === 0 || isProcessing}
            onProceed={onProceed}
            onFilesChange={(files) => {
              setPendingCount(files.length);
              onFilesChange(files);
            }}
          />

          {isProcessing ? (
            <div
              className="absolute inset-4 z-20 flex flex-col items-center justify-center rounded-2xl bg-[#f5f5f5]/92 px-6 text-center backdrop-blur-[1px]"
              role="status"
              aria-live="polite"
            >
              <span
                aria-hidden
                className="mb-3 size-5 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-800"
              />
              <p className="text-sm font-medium text-neutral-800">{processingLabel}</p>
              <p className="mt-1 text-xs text-neutral-500">Please keep this tab open.</p>
            </div>
          ) : null}
        </section>
        <DocumentsSection
          documents={documents}
          onClearAll={clearAllDocuments}
          onOpenDocument={onOpenDocument}
          cardStyle={SOFT_CARD_STYLE}
        />
      </div>
    </div>
  );
}
