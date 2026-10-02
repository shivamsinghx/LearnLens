"use client";

import { useState } from "react";

import { FileUploadFieldInput } from "@/components/inputs/file-upload-field-input";

import { DocumentsSection, type StudyDocument } from "./DocumentsSection";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function StudyMaterials() {
  const [documents, setDocuments] = useState<readonly StudyDocument[]>([]);

  return (
    <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-2">
      <section id="upload" aria-label="Upload study material" className="premium-card font-sans md:p-8">
        <FileUploadFieldInput
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
      <DocumentsSection documents={documents} />
    </div>
  );
}
