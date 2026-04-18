import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUploadProcesso, useAnalyzeProcesso } from '../../api/processes';
import { Icon } from '../../modules/ui/Icon';
import './UploadScreen.css';

type UploadStatus = 'pending' | 'selected' | 'uploaded' | 'missing';

const REQUIRED_DOCUMENTS = [
  { name: 'Case File (Autos)', allowMultiple: true },
  { name: 'Contract', allowMultiple: false },
  { name: 'Statement (Extrato)', allowMultiple: false },
  { name: 'Credit Proof (Comprovante)', allowMultiple: false },
  { name: 'Dossier', allowMultiple: false },
  { name: 'Debt Evolution Statement', allowMultiple: false },
  { name: 'Referenced Report', allowMultiple: false },
] as const;

type UploadListItem = {
  id: number;
  expectedName: string;
  allowMultiple: boolean;
  files: File[];
  status: UploadStatus;
  uploadedAt: string | null;
  uploadDurationMs: number | null;
};

function createInitialUploadList(): UploadListItem[] {
  return REQUIRED_DOCUMENTS.map((document, index) => ({
    id: index + 1,
    expectedName: document.name,
    allowMultiple: document.allowMultiple,
    files: [],
    status: 'pending',
    uploadedAt: null,
    uploadDurationMs: null,
  }));
}

function formatUploadDuration(ms: number | null): string {
  if (ms == null) return '--';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function truncateFileName(fileName: string): string {
  if (fileName.length <= 20) return fileName;
  return `${fileName.slice(0, 20)}...`;
}

function getDocumentFileLabel(item: UploadListItem): string {
  if (item.files.length === 0) return 'No file attached';
  if (item.allowMultiple && item.files.length > 1) return `${item.files.length} files uploaded`;
  return truncateFileName(item.files[0].name);
}

function getDocumentTotalSizeKb(item: UploadListItem): number {
  const totalBytes = item.files.reduce((sum, file) => sum + file.size, 0);
  return Math.round(totalBytes / 1024);
}

function isPdfFile(file: File): boolean {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
}

function getStatusLabel(status: UploadStatus): string {
  if (status === 'uploaded') return 'Uploaded';
  if (status === 'selected') return 'Uploaded';
  if (status === 'missing') return 'Missing';
  return 'Waiting';
}

function getStatusTone(status: UploadStatus): '' | 'success' | 'warning' | 'danger' {
  if (status === 'uploaded') return 'success';
  if (status === 'selected') return 'success';
  if (status === 'missing') return 'danger';
  return '';
}

function getStatusDescription(item: UploadListItem): string {
  if (item.status === 'uploaded') {
    return `Uploaded in ${formatUploadDuration(item.uploadDurationMs)} at ${item.uploadedAt}`;
  }

  if (item.status === 'selected') {
    return 'Document selected and queued for the final upload.';
  }

  if (item.status === 'missing') {
    return 'Document marked as missing.';
  }

  return 'Waiting for this document upload.';
}

export function UploadScreen() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<UploadListItem[]>(() => createInitialUploadList());
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [finalSectionAlert, setFinalSectionAlert] = useState<string | null>(null);
  const [requiresNewFileAfterMetadataFailure, setRequiresNewFileAfterMetadataFailure] = useState(false);

  const upload = useUploadProcesso();
  const analyze = useAnalyzeProcesso();

  const currentDocumentIndex = files.findIndex((item) => item.status === 'pending');
  const currentDocument = currentDocumentIndex >= 0 ? files[currentDocumentIndex] : null;
  const uploadedCount = files.filter((item) => item.status === 'uploaded').length;
  const selectedCount = files.filter((item) => item.status === 'selected').length;
  const missingCount = files.filter((item) => item.status === 'missing').length;
  const hasUploadableSelection = files.some((item) => item.status === 'selected' && item.files.length > 0);
  const canSubmitFinalUpload = hasUploadableSelection && !requiresNewFileAfterMetadataFailure;
  const allDocumentsMissing = !currentDocument && files.every((item) => item.status === 'missing');
  const finalSectionMessage = finalSectionAlert ?? (allDocumentsMissing ? 'At least one PDF is required for upload and analysis.' : null);

  function handleStartNewAnalysis() {
    setFiles(createInitialUploadList());
    setUploadProgress(null);
    setError(null);
    setFinalSectionAlert(null);
    setRequiresNewFileAfterMetadataFailure(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  function getPdfFiles(candidateFiles: File[]): File[] {
    return candidateFiles.filter(isPdfFile);
  }

  function attachFilesToNextStep(selectedFiles: File[]) {
    setFinalSectionAlert(null);
    setRequiresNewFileAfterMetadataFailure(false);
    setFiles((prev) => {
      const nextPendingIndex = prev.findIndex((item) => item.status === 'pending');
      if (nextPendingIndex < 0) return prev;

      const nextPendingItem = prev[nextPendingIndex];
      const filesForCurrentStep = nextPendingItem.allowMultiple ? selectedFiles : [selectedFiles[0]];

      return prev.map((item, index) => {
        if (index !== nextPendingIndex) return item;

        return {
          ...item,
          files: filesForCurrentStep,
          status: 'selected',
          uploadedAt: null,
          uploadDurationMs: null,
        };
      });
    });
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();

    if (!currentDocument) {
      setError('All documents have already been classified.');
      return;
    }

    const pdfFiles = getPdfFiles(Array.from(e.dataTransfer.files));
    if (pdfFiles.length === 0) {
      setError('Upload only one PDF file per step.');
      return;
    }

    if (!currentDocument.allowMultiple && pdfFiles.length > 1) {
      setError('Only one PDF file is allowed for this document type.');
      return;
    }

    setError(null);
    attachFilesToNextStep(pdfFiles);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (!currentDocument) {
      setError('All documents have already been classified.');
      e.target.value = '';
      return;
    }

    if (!e.target.files || e.target.files.length === 0) return;

    const pdfFiles = getPdfFiles(Array.from(e.target.files));
    if (pdfFiles.length === 0) {
      setError('Upload only one PDF file per step.');
      e.target.value = '';
      return;
    }

    if (!currentDocument.allowMultiple && pdfFiles.length > 1) {
      setError('Only one PDF file is allowed for this document type.');
      e.target.value = '';
      return;
    }

    setError(null);
    attachFilesToNextStep(pdfFiles);
    e.target.value = '';
  }

  function skipCurrentDocument() {
    setError(null);
    if (!requiresNewFileAfterMetadataFailure) {
      setFinalSectionAlert(null);
    }
    setFiles((prev) => {
      const nextPendingIndex = prev.findIndex((item) => item.status === 'pending');
      if (nextPendingIndex < 0) return prev;

      return prev.map((item, index) => {
        if (index !== nextPendingIndex) return item;
        return {
          ...item,
          files: [],
          status: 'missing',
          uploadedAt: null,
          uploadDurationMs: null,
        };
      });
    });
  }

  function resetDocument(documentId: number) {
    if (!requiresNewFileAfterMetadataFailure) {
      setFinalSectionAlert(null);
    }
    setFiles((prev) => prev.map((item) => {
      if (item.id !== documentId) return item;
      return {
        ...item,
        files: [],
        status: 'pending',
        uploadedAt: null,
        uploadDurationMs: null,
      };
    }));
  }

  async function handleSubmit() {
    const filesToUpload = files
      .filter((item) => item.status === 'selected' && item.files.length > 0)
      .flatMap((item) => item.files);

    setFinalSectionAlert(null);

    if (filesToUpload.length === 0) {
      setFinalSectionAlert('At least one PDF is required for upload and analysis.');
      return;
    }

    setError(null);
    setUploadProgress(30);
    const uploadStartedAt = performance.now();

    try {
      const processo = await upload.mutateAsync({
        numeroProcesso: `PROC-${Date.now()}`,
        files: filesToUpload,
      });

      if (processo.metadata_extraida == null) {
        setUploadProgress(null);
        setRequiresNewFileAfterMetadataFailure(true);
        setFinalSectionAlert('Metadata extraction failed. Please upload more files and try again.');
        return;
      }

      setRequiresNewFileAfterMetadataFailure(false);

      const uploadDurationMs = Math.round(performance.now() - uploadStartedAt);
      const uploadedAt = new Date().toLocaleTimeString('pt-BR');
      setFiles((prev) => prev.map((item) => ({
        ...item,
        ...(item.status === 'selected'
          ? {
              status: 'uploaded' as const,
              uploadedAt,
              uploadDurationMs,
            }
          : {}),
      })));

      setUploadProgress(60);

      // Trigger AI analysis; if it fails (for example 501), upload is still successful.
      try {
        await analyze.mutateAsync(processo.id);
      } catch (err) {
        console.warn('AI analysis triggered but returned error (expected in dev):', err);
      }

      setUploadProgress(100);
      setTimeout(() => navigate(`/dashboard/${processo.id}`), 400);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload documents. Check your connection and try again.');
      setUploadProgress(null);
    }
  }

  const isLoading = upload.isPending || analyze.isPending;

  return (
    <main className="screen upload-screen">
      <section className="panel panel-inner upload-screen__summary">
        <div className="section-heading upload-screen__heading">
          <div className='upload-screen__title-row-parent'>
            <div className="upload-screen__title-row">
              <h1 className="section-title-strong upload-screen__title">Evidence Hub</h1>
              <button
                type="button"
                className="ghost-button upload-screen__new-analysis-button"
                onClick={handleStartNewAnalysis}
                disabled={isLoading}
              >
                Start New Analysis
              </button>
            </div>
            <p className="section-text upload-screen__subtitle">Centralize and process legal documentation for automated compliance analysis.</p>
          </div>
        </div>

        <div className="metric-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {uploadProgress !== null && (
            <div>
              <div className="section-heading upload-screen__progress-heading">
                <div className="doc-main upload-screen__analyzing-copy">
                  <div className="mini-icon upload-screen__pulse-icon"><Icon name="auto_awesome" /></div>
                  <div>
                    <h3 className="section-title-strong upload-screen__progress-title">
                      {uploadProgress < 100 ? 'Processing Evidence…' : 'Done — opening Decision Lab'}
                    </h3>
                    <p className="section-text upload-screen__progress-subtitle">
                      {uploadProgress < 60 ? 'Uploading documents…' : uploadProgress < 100 ? 'Triggering AI analysis…' : 'Redirecting…'}
                    </p>
                  </div>
                </div>
                <strong className="upload-screen__progress-value">{uploadProgress}%</strong>
              </div>
              <div className="progress"><span style={{ width: `${uploadProgress}%`, transition: 'width 0.4s ease' }} /></div>
            </div>
          )}
        </div>
      </section>

      <div className="upload-grid upload-screen__grid">
        <section
          className="panel panel-inner upload-screen__drop-column"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
        >
          <div className="section-heading">
            <span className="section-title">Case Files and Evidence</span>
            <span className="muted" style={{ fontSize: '0.82rem' }}>
              {uploadedCount} uploaded • {selectedCount} uploaded (queued) • {missingCount} missing
            </span>
          </div>
          <div className="upload-zone upload-screen__drop-zone">
            <div>
              <div className="upload-icon upload-screen__drop-icon">
                <Icon name="upload_file" />
              </div>
              <h2 className="section-title-strong upload-screen__drop-title">
                {currentDocument ? `Upload: ${currentDocument.expectedName}` : 'Sequence completed'}
              </h2>
              <p className="section-text upload-screen__drop-copy">
                {currentDocument
                  ? `Step ${currentDocumentIndex + 1} of ${files.length}. This area accepts one PDF at a time.`
                  : 'All required documents were classified. Review the list and submit for analysis.'}
              </p>
              {!currentDocument && finalSectionMessage && (
                <p className="upload-screen__final-warning" role="alert">
                  {finalSectionMessage}
                </p>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                multiple={currentDocument?.allowMultiple ?? false}
                hidden
                onChange={handleFileChange}
              />
              {currentDocument ? (
                <div style={{ display: 'flex', justifyContent: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <button
                    className="primary-button"
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading || uploadProgress !== null}
                  >
                    Select PDF
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={skipCurrentDocument}
                    disabled={isLoading || uploadProgress !== null}
                  >
                    Skip and mark missing
                  </button>
                </div>
              ) : (
                canSubmitFinalUpload ? (
                  <button
                    className="primary-button"
                    type="button"
                    onClick={handleSubmit}
                    disabled={isLoading || uploadProgress !== null}
                  >
                    {isLoading ? 'Sending...' : 'Upload and Analyze'}
                  </button>
                ) : null
              )}
            </div>
          </div>
        </section>

        <section className="panel panel-inner upload-screen__evidence-column">
          <div className="section-heading"><span className="section-title">Processed</span></div>
          <div className="activity-list upload-screen__processed-list">
            {files.map((item) => (
              <div key={item.id} className="activity-item upload-screen__recent-item">
                <div className="activity-main">
                  <div className="doc-icon"><Icon name="picture_as_pdf" /></div>
                  <div className="upload-screen__recent-content">
                    <strong className="upload-screen__recent-title" style={{ fontSize: '0.85rem' }}>{item.expectedName}</strong>
                    <p className="muted upload-screen__recent-meta upload-screen__recent-file-name">{getDocumentFileLabel(item)}</p>
                    {item.files.length > 0 && <p className="muted upload-screen__recent-meta">{getDocumentTotalSizeKb(item)} KB</p>}
                    <p className="muted upload-screen__recent-meta">{getStatusDescription(item)}</p>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`status-pill ${getStatusTone(item.status)}`.trim()}>
                    {getStatusLabel(item.status)}
                  </span>
                  <button
                    type="button"
                    className="icon-button upload-screen__reset-button"
                    onClick={() => resetDocument(item.id)}
                    aria-label={`Reset ${item.expectedName}`}
                    disabled={isLoading || uploadProgress !== null}
                  >
                    <Icon name="close" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {error && <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: 8 }}>{error}</p>}
        </section>
      </div>
    </main>
  );
}
