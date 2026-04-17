import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUploadProcesso, useAnalyzeProcesso } from '../../api/processes';
import { Icon } from '../../modules/ui/Icon';
import './UploadScreen.css';

export function UploadScreen() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [numeroProcesso, setNumeroProcesso] = useState('');
  const [valorCausa, setValorCausa] = useState('');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const upload = useUploadProcesso();
  const analyze = useAnalyzeProcesso();

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files).filter((f) => f.type === 'application/pdf');
    setFiles((prev) => [...prev, ...dropped]);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit() {
    if (!numeroProcesso.trim()) { setError('Informe o número do processo.'); return; }
    if (files.length === 0) { setError('Adicione ao menos um documento PDF.'); return; }
    setError(null);
    setUploadProgress(30);

    try {
      const processo = await upload.mutateAsync({
        numeroProcesso: numeroProcesso.trim(),
        valorCausa: valorCausa ? parseFloat(valorCausa) : undefined,
        files,
      });
      setUploadProgress(60);

      // Dispara a análise IA (DEV-2 implementa o pipeline; enquanto isso navega direto)
      try {
        await analyze.mutateAsync(processo.id);
      } catch {
        // Pipeline ainda em desenvolvimento — navega mesmo assim
      }

      setUploadProgress(100);
      setTimeout(() => navigate(`/dashboard/${processo.id}`), 400);
    } catch {
      setError('Falha ao enviar os documentos. Verifique a conexão e tente novamente.');
      setUploadProgress(null);
    }
  }

  const isLoading = upload.isPending || analyze.isPending;

  return (
    <main className="screen upload-screen">
      <section className="panel panel-inner upload-screen__summary">
        <div className="section-heading upload-screen__heading">
          <div>
            <h1 className="section-title-strong upload-screen__title">Evidence Hub</h1>
            <p className="section-text upload-screen__subtitle">Centralize and process legal documentation for automated adherence analysis.</p>
          </div>
          <button type="button" className="ghost-button" onClick={() => navigate('/dashboard')}>
            Return to Decision Lab
          </button>
        </div>

        <div className="metric-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label className="field-label" style={{ display: 'block', marginBottom: 4 }}>Process Number *</label>
              <div className="input-row">
                <Icon name="tag" className="icon-prefix" />
                <input
                  className="text-input" type="text"
                  placeholder="0801234-56-2024-8-10-0001"
                  value={numeroProcesso}
                  onChange={(e) => setNumeroProcesso(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label className="field-label" style={{ display: 'block', marginBottom: 4 }}>Valor da Causa (R$)</label>
              <div className="input-row">
                <Icon name="payments" className="icon-prefix" />
                <input
                  className="text-input" type="number" placeholder="15000"
                  value={valorCausa} onChange={(e) => setValorCausa(e.target.value)}
                />
              </div>
            </div>
          </div>

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
            <span className="section-title">Autos & Subsídios</span>
            <span className="muted" style={{ fontSize: '0.82rem' }}>{files.length} file(s)</span>
          </div>
          <div className="upload-zone upload-screen__drop-zone">
            <div>
              <div className="upload-icon upload-screen__drop-icon">
                <Icon name="upload_file" style={{ fontSize: '2.4rem' }} />
              </div>
              <h2 className="section-title-strong upload-screen__drop-title">Drop PDFs here</h2>
              <p className="section-text upload-screen__drop-copy">Petição inicial, procuração, contrato, extrato, dossiê…</p>
              <input ref={fileInputRef} type="file" accept=".pdf" multiple hidden onChange={handleFileChange} />
              <button className="primary-button" type="button" onClick={() => fileInputRef.current?.click()}>
                Browse Files
              </button>
            </div>
          </div>
        </section>

        <section className="panel panel-inner upload-screen__evidence-column">
          <div className="section-heading"><span className="section-title">Selected Documents</span></div>
          {files.length === 0 ? (
            <p className="muted" style={{ padding: '1rem 0' }}>No files selected yet.</p>
          ) : (
            <div className="activity-list">
              {files.map((f, i) => (
                <div key={i} className="activity-item upload-screen__recent-item">
                  <div className="activity-main">
                    <div className="doc-icon"><Icon name="picture_as_pdf" /></div>
                    <div>
                      <strong style={{ fontSize: '0.85rem' }}>{f.name}</strong>
                      <p className="muted upload-screen__recent-meta">{(f.size / 1024).toFixed(0)} KB</p>
                    </div>
                  </div>
                  <button type="button" className="icon-button" onClick={() => removeFile(i)}>
                    <Icon name="close" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {error && <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: 8 }}>{error}</p>}

          <button
            type="button" className="primary-button" style={{ marginTop: 16, width: '100%' }}
            onClick={handleSubmit} disabled={isLoading || uploadProgress !== null}
          >
            {isLoading ? 'Sending…' : 'Upload & Analyze'}
          </button>
        </section>
      </div>
    </main>
  );
}
