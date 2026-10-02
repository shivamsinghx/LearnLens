"use client";

import { useState, type CSSProperties } from "react";

import { FileUploadFieldInput } from "@/components/inputs/file-upload-field-input";
import { WavyDotGrid } from "@/components/ui/wavy-dot-grid";

import { DocumentsSection, type StudyDocument } from "./DocumentsSection";

/** Soft UI / neumorphic — same dual-shadow language as SoftUiButton.
 * Needs a matching #f5f5f5 surround so the light highlight reads. */
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function StudyMaterials() {
  const [documents, setDocuments] = useState<readonly StudyDocument[]>([]);
  const [uploadKey, setUploadKey] = useState(0);

  const clearAllDocuments = () => {
    setDocuments([]);
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
          className="font-sans md:p-8"
          style={SOFT_CARD_STYLE}
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
            onFilesChange={(files) => {
              setDocuments(
                files.map((file) => ({
                  id: `${file.name}-${file.size}-${file.lastModified}`,
                  name: file.name,
                  sizeLabel: formatFileSize(file.size),
                })),
              );
            }}
          />
        </section>
        <DocumentsSection
          documents={documents}
          onClearAll={clearAllDocuments}
          cardStyle={SOFT_CARD_STYLE}
        />
      </div>
    </div>
  );
}
