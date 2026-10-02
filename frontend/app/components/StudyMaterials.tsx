"use client";

import { useState, type CSSProperties } from "react";

import { FileUploadFieldInput } from "@/components/inputs/file-upload-field-input";

import { DocumentsSection, type StudyDocument } from "./DocumentsSection";

/** Soft UI / neumorphic — same dual-shadow language as SoftUiButton.
 * Needs a matching #f5f5f5 surround so the light highlight reads. */
const SOFT_CARD_STYLE: CSSProperties = {
  borderRadius: "1.5rem",
  border: "none",
  background: "#f5f5f5",
  padding: "1.75rem",
  boxShadow: "10px 10px 20px #d1d1d1, -10px -10px 20px #ffffff",
};

const SOFT_SURFACE_STYLE: CSSProperties = {
  borderRadius: "2rem",
  background: "#f5f5f5",
  padding: "1.25rem",
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
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2 lg:gap-7">
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
