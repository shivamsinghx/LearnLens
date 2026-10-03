import { apiBaseUrl } from "@/app/lib/api";
import {
  formatFileSize,
  type StudyDocument,
} from "@/app/lib/study-document";

export type UploadedDocumentMeta = {
  readonly id: string;
  readonly filename: string;
  readonly size_bytes: number;
  readonly status: "uploaded";
  readonly uploaded_at: string;
  readonly stored_filename: string;
};

export type UploadDocumentError = {
  readonly filename: string;
  readonly detail: string;
};

export type UploadDocumentsResult = {
  readonly documents: readonly StudyDocument[];
  readonly errors: readonly UploadDocumentError[];
};

type UploadResponsePayload = {
  readonly documents: readonly UploadedDocumentMeta[];
  readonly errors?: readonly UploadDocumentError[];
};

export class UploadDocumentsError extends Error {
  readonly status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = "UploadDocumentsError";
    this.status = status;
  }
}

function isUploadedDocumentMeta(value: unknown): value is UploadedDocumentMeta {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    typeof record.filename === "string" &&
    typeof record.size_bytes === "number" &&
    record.status === "uploaded" &&
    typeof record.uploaded_at === "string" &&
    typeof record.stored_filename === "string"
  );
}

function studyDocumentFromUpload(
  meta: UploadedDocumentMeta,
  file: File | undefined,
): StudyDocument {
  return {
    id: meta.id,
    name: meta.filename,
    sizeLabel: formatFileSize(meta.size_bytes),
    sizeBytes: meta.size_bytes,
    uploadedAt: meta.uploaded_at,
    status: "ready",
    objectUrl: file ? URL.createObjectURL(file) : "",
  };
}

export async function uploadDocuments(
  files: readonly File[],
): Promise<UploadDocumentsResult> {
  if (files.length === 0) {
    throw new UploadDocumentsError("Select at least one PDF to upload.");
  }

  const body = new FormData();
  for (const file of files) {
    body.append("files", file, file.name);
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}/api/v1/documents/upload`, {
      method: "POST",
      body,
    });
  } catch {
    throw new UploadDocumentsError(
      "Could not reach the LearnLens API. Is the backend running?",
    );
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof (payload as { detail: unknown }).detail === "string"
        ? (payload as { detail: string }).detail
        : `Upload failed (${response.status}).`;
    throw new UploadDocumentsError(detail, response.status);
  }

  if (
    typeof payload !== "object" ||
    payload === null ||
    !Array.isArray((payload as UploadResponsePayload).documents)
  ) {
    throw new UploadDocumentsError("Unexpected upload response from the API.");
  }

  const data = payload as UploadResponsePayload;
  const byName = new Map(files.map((file) => [file.name, file]));

  const documents = data.documents.filter(isUploadedDocumentMeta).map((meta) => {
    const match =
      byName.get(meta.filename) ??
      files.find((file) => file.name === meta.filename);
    return studyDocumentFromUpload(meta, match);
  });

  if (documents.length === 0) {
    throw new UploadDocumentsError("No valid PDF files were uploaded.");
  }

  return {
    documents,
    errors: Array.isArray(data.errors) ? data.errors : [],
  };
}
