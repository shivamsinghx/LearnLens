export type StudyDocument = {
  readonly id: string;
  readonly name: string;
  readonly sizeLabel: string;
  readonly sizeBytes: number;
  readonly uploadedAt: string;
  readonly status: "ready" | "processing";
  /** Object URL for in-browser PDF preview — revoke on remove/clear. */
  readonly objectUrl: string;
};

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function createStudyDocument(file: File): StudyDocument {
  return {
    id: `${file.name}-${file.size}-${file.lastModified}`,
    name: file.name,
    sizeLabel: formatFileSize(file.size),
    sizeBytes: file.size,
    uploadedAt: new Date().toISOString(),
    status: "ready",
    objectUrl: URL.createObjectURL(file),
  };
}

export function revokeStudyDocument(doc: StudyDocument) {
  if (doc.objectUrl) URL.revokeObjectURL(doc.objectUrl);
}

export function documentTitle(name: string): string {
  return name.replace(/\.pdf$/i, "").trim() || name;
}
