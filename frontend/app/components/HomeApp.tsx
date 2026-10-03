"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  createLocalStudyDocument,
  revokeStudyDocument,
  type StudyDocument,
} from "@/app/lib/study-document";
import {
  UploadDocumentsError,
  uploadDocuments,
} from "@/app/lib/upload-documents";

import { DocumentWorkspace } from "./DocumentWorkspace";
import { LandingPage } from "./LandingPage";

export function HomeApp() {
  const [documents, setDocuments] = useState<readonly StudyDocument[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [processingLabel, setProcessingLabel] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const pendingFilesRef = useRef<File[]>([]);
  const documentsRef = useRef(documents);
  documentsRef.current = documents;

  useEffect(() => {
    return () => {
      for (const doc of documentsRef.current) revokeStudyDocument(doc);
    };
  }, []);

  const replaceDocuments = useCallback((next: readonly StudyDocument[]) => {
    setDocuments((prev) => {
      const keep = new Set(next.map((doc) => doc.objectUrl).filter(Boolean));
      for (const doc of prev) {
        if (doc.objectUrl && !keep.has(doc.objectUrl)) revokeStudyDocument(doc);
      }
      return next;
    });
  }, []);

  const handleFilesChange = useCallback(
    (files: File[]) => {
      pendingFilesRef.current = files;
      setUploadError(null);
      // Local preview only — backend metadata replaces this on Proceed.
      const next = files.map(createLocalStudyDocument);
      replaceDocuments(next);
      setActiveDocumentId(next[0]?.id ?? null);
      setWorkspaceOpen(false);
    },
    [replaceDocuments],
  );

  const handleProceed = useCallback(async () => {
    const files = pendingFilesRef.current;
    if (files.length === 0) return;

    setUploadError(null);
    setProcessingLabel("Uploading...");

    try {
      const result = await uploadDocuments(files);
      replaceDocuments(result.documents);
      setActiveDocumentId(result.documents[0]?.id ?? null);
      pendingFilesRef.current = [];

      if (result.errors.length > 0) {
        const failed = result.errors
          .map((item) => `${item.filename}: ${item.detail}`)
          .join(" ");
        setUploadError(`Some files were skipped. ${failed}`);
      }

      setProcessingLabel(null);
      setWorkspaceOpen(true);
    } catch (error) {
      const message =
        error instanceof UploadDocumentsError
          ? error.message
          : "Upload failed. Please try again.";
      setUploadError(message);
      setProcessingLabel(null);
      setWorkspaceOpen(false);
    }
  }, [replaceDocuments]);

  const handleClearAll = useCallback(() => {
    pendingFilesRef.current = [];
    replaceDocuments([]);
    setActiveDocumentId(null);
    setProcessingLabel(null);
    setUploadError(null);
    setWorkspaceOpen(false);
  }, [replaceDocuments]);

  const handleAddFiles = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      setUploadError(null);
      setProcessingLabel("Uploading...");

      try {
        const result = await uploadDocuments(files);
        setDocuments((prev) => {
          const byId = new Map(prev.map((doc) => [doc.id, doc]));
          for (const doc of result.documents) {
            const existing = byId.get(doc.id);
            if (existing) revokeStudyDocument(doc);
            else byId.set(doc.id, doc);
          }
          return Array.from(byId.values());
        });
        setActiveDocumentId((current) => current ?? result.documents[0]?.id ?? null);

        if (result.errors.length > 0) {
          const failed = result.errors
            .map((item) => `${item.filename}: ${item.detail}`)
            .join(" ");
          setUploadError(`Some files were skipped. ${failed}`);
        }
      } catch (error) {
        const message =
          error instanceof UploadDocumentsError
            ? error.message
            : "Upload failed. Please try again.";
        setUploadError(message);
      } finally {
        setProcessingLabel(null);
      }
    },
    [],
  );

  if (workspaceOpen && documents.length > 0) {
    return (
      <DocumentWorkspace
        documents={documents}
        activeDocumentId={activeDocumentId}
        onSelectDocument={setActiveDocumentId}
        onAddFiles={(files) => {
          void handleAddFiles(files);
        }}
        onGoHome={() => {
          setUploadError(null);
          setWorkspaceOpen(false);
        }}
      />
    );
  }

  return (
    <LandingPage
      documents={documents}
      processingLabel={processingLabel}
      uploadError={uploadError}
      onFilesChange={handleFilesChange}
      onProceed={() => {
        void handleProceed();
      }}
      onClearAll={handleClearAll}
      onOpenDocument={(id) => {
        // Only open workspace for documents that were uploaded to the API.
        if (!id.startsWith("local-")) {
          setActiveDocumentId(id);
          setWorkspaceOpen(true);
        }
      }}
    />
  );
}
