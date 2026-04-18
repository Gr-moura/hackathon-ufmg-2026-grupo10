import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  useAnalysis,
  useAnalyzeProcesso,
  useProcesso,
  useRegisterDecision,
} from '../../api/processes';
import type { AcaoAdvogado, AnaliseIAResponse } from '../../api/types';
import { Icon } from '../../modules/ui/Icon';
import './DashboardScreen.css';

const BRL = (value: number | null | undefined) =>
  value != null
    ? value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
    : '—';

const PCT = (value: number | null | undefined) =>
  value != null ? `${Math.round(value * 100)}%` : '—';

function decisionTone(decisao: string): 'success' | 'warning' | 'danger' | 'neutral' {
  if (decisao === 'ACORDO') return 'success';
  if (decisao === 'DEFESA') return 'warning';
  return 'neutral';
}

function confidenceTone(confidence: number): 'success' | 'warning' | 'danger' {
  if (confidence >= 0.85) return 'success';
  if (confidence >= 0.6) return 'warning';
  return 'danger';
}

export function DashboardScreen() {
  const navigate = useNavigate();
  const { processoId } = useParams<{ processoId: string }>();

  const processoQuery = useProcesso(processoId);
  const analysisQuery = useAnalysis(processoId);
  const analyze = useAnalyzeProcesso();
  const registerDecision = useRegisterDecision();

  const analysisError = analysisQuery.error as { response?: { status?: number } } | null;
  const shouldAutoTrigger =
    !!processoId &&
    !analysisQuery.data &&
    !analysisQuery.isLoading &&
    analysisError?.response?.status === 404 &&
    !analyze.isPending &&
    !analyze.isError;

  useEffect(() => {
    if (shouldAutoTrigger && processoId) {
      analyze.mutate(processoId, {
        onSuccess: () => analysisQuery.refetch(),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldAutoTrigger, processoId]);

  const analysis: AnaliseIAResponse | undefined = analysisQuery.data;

  if (!processoId) {
    return (
      <main className="screen dashboard-screen">
        <section className="panel panel-inner hero-banner dashboard-screen__hero">
          <div className="title-kicker">Decision Lab</div>
          <h1 className="headline dashboard-screen__headline">Select a case to review</h1>
          <p className="lede dashboard-screen__lede">
            Open a case from Monitoring or start a new analysis from the Evidence Hub to review the
            AI recommendation here.
          </p>
          <div className="dashboard-screen__actions">
            <button type="button" className="primary-button" onClick={() => navigate('/upload')}>
              <Icon name="upload_file" /> New Analysis
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => navigate('/monitoring')}
            >
              <Icon name="analytics" /> Open Monitoring
            </button>
          </div>
        </section>
      </main>
    );
  }

  if (processoQuery.isLoading) {
    return (
      <main className="screen dashboard-screen">
        <p className="muted">Loading case…</p>
      </main>
    );
  }

  if (processoQuery.isError) {
    return (
      <main className="screen dashboard-screen">
        <section className="panel panel-inner hero-banner dashboard-screen__hero">
          <div className="title-kicker">Decision Lab</div>
          <h1 className="headline dashboard-screen__headline">Case not found</h1>
          <p className="lede dashboard-screen__lede">
            The requested case could not be loaded. It may have been removed or you may not have
            permission to view it.
          </p>
          <button type="button" className="primary-button" onClick={() => navigate('/monitoring')}>
            <Icon name="arrow_back" /> Back to Monitoring
          </button>
        </section>
      </main>
    );
  }

  const processo = processoQuery.data;
  const analysisRunning = analyze.isPending || analysisQuery.isLoading;

  return (
    <main className="screen dashboard-screen">
      <div className="hero-grid dashboard-screen__grid">
        <section className="panel panel-inner hero-banner dashboard-screen__hero">
          <div className="title-kicker">AI Analysis Outcome</div>
          <h1 className="headline dashboard-screen__headline">
            {processo ? processo.numero_processo : 'Case Analysis'}
          </h1>
          <p className="lede dashboard-screen__lede">
            {analysis
              ? analysis.rationale
              : analysisRunning
              ? 'Running the AI pipeline across the submitted evidence…'
              : 'No AI analysis available yet for this case.'}
          </p>

          {analysis && (
            <div className="dashboard-screen__decision-row">
              <span className={`status-pill ${decisionTone(analysis.decisao)}`}>
                {analysis.decisao === 'ACORDO' ? 'Settlement' : 'Defense'}
              </span>
              <span className={`status-pill ${confidenceTone(analysis.confidence)}`}>
                Confidence {PCT(analysis.confidence)}
              </span>
              {analysis.requires_supervisor && (
                <span className="status-pill danger">Supervisor review required</span>
              )}
            </div>
          )}

          {analysis?.proposta && (
            <div className="split-grid dashboard-screen__split">
              <div className="metric-card">
                <div className="metric-label">Suggested Settlement</div>
                <h3 className="metric-value" style={{ fontSize: '1.9rem' }}>
                  <span style={{ color: 'var(--primary)' }}>
                    {BRL(analysis.proposta.valor_sugerido)}
                  </span>
                </h3>
                <div className="metric-note">
                  Range {BRL(analysis.proposta.intervalo_min)} – {BRL(analysis.proposta.intervalo_max)}
                </div>
              </div>

              <div className="metric-card dashboard-screen__cost-card">
                <div className="section-heading" style={{ marginBottom: 10 }}>
                  <span className="metric-label">Estimated Litigation Cost</span>
                  <strong>{BRL(analysis.proposta.custo_estimado_litigar)}</strong>
                </div>
                <div className="progress">
                  <span
                    style={{
                      width: `${Math.min(
                        100,
                        Math.round(
                          (analysis.proposta.valor_sugerido /
                            Math.max(analysis.proposta.custo_estimado_litigar, 1)) *
                            100,
                        ),
                      )}%`,
                    }}
                  />
                </div>
                <p className="muted dashboard-screen__cost-copy">
                  Expected savings: {BRL(analysis.proposta.economia_esperada)}
                  {analysis.proposta.n_casos_similares > 0 && (
                    <> • Based on {analysis.proposta.n_casos_similares} similar cases</>
                  )}
                </p>
              </div>
            </div>
          )}

          {!analysis && analysisRunning && (
            <p className="muted">⏳ The pipeline usually takes a few seconds per case.</p>
          )}

          {!analysis && !analysisRunning && (
            <button
              type="button"
              className="primary-button"
              onClick={() => processoId && analyze.mutate(processoId, { onSuccess: () => analysisQuery.refetch() })}
            >
              <Icon name="auto_awesome" /> Run AI analysis
            </button>
          )}
        </section>

        <aside className="panel panel-inner dashboard-screen__aside">
          <div className="section-heading">
            <h3 className="section-title">Analyzed Documents</h3>
            <Icon name="filter_list" />
          </div>
          <div className="doc-list">
            {processo?.documentos?.length ? (
              processo.documentos.map((doc) => {
                const hasErrors = (doc.parse_errors?.length ?? 0) > 0;
                return (
                  <div key={doc.id} className="doc-item">
                    <div className="doc-main">
                      <div className="doc-icon">
                        <Icon name="description" />
                      </div>
                      <div>
                        <strong>{doc.original_filename}</strong>
                        <div className="muted" style={{ fontSize: '0.78rem' }}>
                          {doc.doc_type} • {doc.page_count} pages
                        </div>
                      </div>
                    </div>
                    <span className={`status-pill ${hasErrors ? 'danger' : 'success'}`}>
                      {hasErrors ? 'Parse issue' : 'Ingested'}
                    </span>
                  </div>
                );
              })
            ) : (
              <p className="muted">No documents attached to this case.</p>
            )}
          </div>

          {analysis && (
            <div className="glass-card dashboard-screen__audit" style={{ marginTop: 18 }}>
              <div className="section-heading" style={{ marginBottom: 8 }}>
                <div className="doc-main" style={{ gap: 10 }}>
                  <Icon name="info" />
                  <h4 className="section-title-strong" style={{ fontSize: '0.9rem' }}>
                    Key Factors
                  </h4>
                </div>
              </div>
              {analysis.fatores_pro_acordo.length > 0 && (
                <p className="muted" style={{ margin: 0, fontSize: '0.82rem', lineHeight: 1.6 }}>
                  <strong style={{ color: 'var(--success)' }}>Pro-settlement:</strong>{' '}
                  {analysis.fatores_pro_acordo.join(', ')}
                </p>
              )}
              {analysis.fatores_pro_defesa.length > 0 && (
                <p className="muted" style={{ margin: 0, fontSize: '0.82rem', lineHeight: 1.6 }}>
                  <strong style={{ color: 'var(--danger)' }}>Pro-defense:</strong>{' '}
                  {analysis.fatores_pro_defesa.join(', ')}
                </p>
              )}
            </div>
          )}
        </aside>
      </div>

      {analysis && (
        <LawyerDecisionPanel
          analysis={analysis}
          onSubmit={(payload) =>
            registerDecision.mutateAsync({ analiseId: analysis.id, ...payload })
          }
          isSubmitting={registerDecision.isPending}
          submitted={registerDecision.isSuccess}
          errorMessage={
            (registerDecision.error as { response?: { data?: { detail?: string } } } | null)
              ?.response?.data?.detail ?? null
          }
        />
      )}

      {analysis?.trechos_chave?.length ? (
        <section className="panel panel-inner dashboard-screen__risk" style={{ marginTop: 24 }}>
          <div className="section-heading">
            <h3 className="section-title">Evidence Highlights</h3>
          </div>
          <div className="doc-list">
            {analysis.trechos_chave.map((t, idx) => (
              <article key={`${t.doc}-${idx}`} className="doc-item">
                <div className="doc-main">
                  <div className="doc-icon">
                    <Icon name="format_quote" />
                  </div>
                  <div>
                    <strong>{t.doc}</strong>
                    <p
                      className="muted"
                      style={{ margin: '4px 0 0', fontSize: '0.82rem', lineHeight: 1.5 }}
                    >
                      "{t.quote}"
                    </p>
                  </div>
                </div>
                <span className="status-pill neutral">Page {t.page}</span>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}

interface LawyerDecisionPanelProps {
  analysis: AnaliseIAResponse;
  onSubmit: (payload: {
    acao: AcaoAdvogado;
    valor_advogado: number | null;
    justificativa: string | null;
  }) => Promise<unknown>;
  isSubmitting: boolean;
  submitted: boolean;
  errorMessage: string | null;
}

function LawyerDecisionPanel({
  analysis,
  onSubmit,
  isSubmitting,
  submitted,
  errorMessage,
}: LawyerDecisionPanelProps) {
  const suggested = analysis.proposta?.valor_sugerido ?? null;
  const [acao, setAcao] = useState<AcaoAdvogado>('ACEITAR');
  const [valorAdvogado, setValorAdvogado] = useState<string>(
    suggested != null ? String(suggested) : '',
  );
  const [justificativa, setJustificativa] = useState<string>('');
  const [localError, setLocalError] = useState<string | null>(null);

  const deltaPct = useMemo(() => {
    if (acao !== 'AJUSTAR' || !suggested) return null;
    const parsed = Number(valorAdvogado);
    if (!Number.isFinite(parsed) || parsed <= 0) return null;
    return Math.abs(parsed - suggested) / suggested;
  }, [acao, valorAdvogado, suggested]);

  const requiresJustification = deltaPct != null && deltaPct > 0.15;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLocalError(null);

    let valorPayload: number | null = null;
    if (acao === 'AJUSTAR') {
      const parsed = Number(valorAdvogado);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        setLocalError('Informe um valor válido para ajustar a proposta.');
        return;
      }
      valorPayload = parsed;
    }

    if (requiresJustification && !justificativa.trim()) {
      setLocalError('Justificativa obrigatória quando o ajuste supera 15% do valor sugerido.');
      return;
    }

    try {
      await onSubmit({
        acao,
        valor_advogado: valorPayload,
        justificativa: justificativa.trim() || null,
      });
    } catch {
      // error is surfaced via errorMessage prop
    }
  }

  return (
    <section className="panel panel-inner dashboard-screen__risk" style={{ marginTop: 24 }}>
      <div className="section-heading">
        <h3 className="section-title">Lawyer Decision</h3>
        {submitted && <span className="status-pill success">Decision registered</span>}
      </div>

      <form className="dashboard-screen__decision-form" onSubmit={handleSubmit}>
        <div className="dashboard-screen__action-row">
          {(['ACEITAR', 'AJUSTAR', 'RECUSAR'] as AcaoAdvogado[]).map((option) => (
            <label
              key={option}
              className={`dashboard-screen__action-chip ${acao === option ? 'active' : ''}`}
            >
              <input
                type="radio"
                name="decision-action"
                value={option}
                checked={acao === option}
                onChange={() => setAcao(option)}
              />
              <span>{option}</span>
            </label>
          ))}
        </div>

        {acao === 'AJUSTAR' && (
          <label className="dashboard-screen__field">
            <span>Adjusted settlement value (BRL)</span>
            <input
              type="number"
              step="0.01"
              min="0"
              value={valorAdvogado}
              onChange={(event) => setValorAdvogado(event.target.value)}
              placeholder={suggested != null ? String(suggested) : 'Value'}
            />
            {suggested != null && deltaPct != null && (
              <small
                className={requiresJustification ? 'text-danger' : 'muted'}
                style={{ marginTop: 4, display: 'block' }}
              >
                Delta vs suggested: {Math.round(deltaPct * 100)}%
                {requiresJustification && ' — justification required'}
              </small>
            )}
          </label>
        )}

        <label className="dashboard-screen__field">
          <span>
            Justification{' '}
            {requiresJustification && <strong className="text-danger">(required)</strong>}
          </span>
          <textarea
            rows={3}
            value={justificativa}
            onChange={(event) => setJustificativa(event.target.value)}
            placeholder="Notes that will stay in the audit trail."
          />
        </label>

        {(localError || errorMessage) && (
          <p className="text-danger" style={{ margin: 0 }}>
            {localError || errorMessage}
          </p>
        )}

        <div className="dashboard-screen__actions">
          <button type="submit" className="primary-button" disabled={isSubmitting}>
            <Icon name="check_circle" />
            {isSubmitting ? 'Saving…' : 'Register decision'}
          </button>
        </div>
      </form>
    </section>
  );
}
