import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAnalysis, useRegisterDecision, useAnalyzeProcesso, useProcessos, useProcesso } from '../../api/processes';
import { Icon } from '../../modules/ui/Icon';
import { dashboardDocs, riskIndicators } from '../../data';
import './DashboardScreen.css';

const BRL = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 85 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--danger)';
  const label = pct >= 85 ? 'High Confidence' : pct >= 60 ? 'Review Advised' : 'Supervisor Required';
  return (
    <span style={{ color, fontWeight: 700, fontSize: '0.85rem' }}>
      {pct}% — {label}
    </span>
  );
}

function MetadataPanel({ meta }: { meta: { uf: string | null; sub_assunto: string | null; valor_da_causa: number | null } | null | undefined }) {
  const none = <span className="muted">não identificado</span>;
  return (
    <div className="panel panel-inner" style={{ marginTop: 16, padding: '1.2rem' }}>
      <div className="field-label" style={{ marginBottom: 12 }}>Metadados extraídos dos PDFs</div>
      {!meta ? (
        <p className="muted">Nenhum metadado extraído.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <tbody>
            <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.08)' }}>
              <td style={{ padding: '8px 12px', fontWeight: 600 }}>UF</td>
              <td style={{ padding: '8px 12px' }}>{meta.uf ?? none}</td>
            </tr>
            <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.08)' }}>
              <td style={{ padding: '8px 12px', fontWeight: 600 }}>Sub-assunto</td>
              <td style={{ padding: '8px 12px' }}>{meta.sub_assunto ? meta.sub_assunto.toUpperCase() : none}</td>
            </tr>
            <tr>
              <td style={{ padding: '8px 12px', fontWeight: 600 }}>Valor da causa</td>
              <td style={{ padding: '8px 12px' }}>
                {meta.valor_da_causa != null
                  ? meta.valor_da_causa.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                  : none}
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}

export function DashboardScreen() {
  const navigate = useNavigate();
  const { processoId } = useParams<{ processoId: string }>();

  const { data: analise, isLoading: loadingAnalysis, error: analysisError } = useAnalysis(processoId);
  const { data: processos, isLoading: loadingList } = useProcessos();
  const { data: processo } = useProcesso(processoId);
  const registerDecision = useRegisterDecision();
  const analyze = useAnalyzeProcesso();
  
  const [justificativa, setJustificativa] = useState('');
  const [valorAjuste, setValorAjuste] = useState('');
  const [decided, setDecided] = useState(false);

  async function handleDecision(acao: 'ACEITAR' | 'AJUSTAR' | 'RECUSAR') {
    if (!analise) return;
    await registerDecision.mutateAsync({
      analiseId: analise.id,
      acao,
      valor_advogado: acao === 'AJUSTAR' && valorAjuste ? parseFloat(valorAjuste) : analise.proposta?.valor_sugerido,
      justificativa: justificativa || null,
    });
    setDecided(true);
  }

  async function handleTriggerAnalysis() {
    if (!processoId) return;
    await analyze.mutateAsync(processoId);
  }

  // ── Render List (Decision Lab) if no ID ───────────────────────────────────
  if (!processoId) {
    return (
      <main className="screen dashboard-screen">
        <section className="panel panel-inner hero-banner">
          <div className="title-kicker">Operational Workflow</div>
          <h1 className="headline">Decision Lab</h1>
          <p className="lede">Manage incoming cases and track AI recommendation status.</p>
        </section>

        <div className="panel panel-inner" style={{ marginTop: 24 }}>
          <div className="section-heading">
            <h3 className="section-title">Active Processes</h3>
            <button className="primary-button" onClick={() => navigate('/upload')}>
              <Icon name="playlist_add" /> New Analysis
            </button>
          </div>

          <div className="activity-list" style={{ marginTop: 16 }}>
            {loadingList ? (
              <p className="muted">Loading processes…</p>
            ) : processos?.length === 0 ? (
              <p className="muted">No processes found. Start by uploading legal documents.</p>
            ) : (
              processos?.map((p) => (
                <div key={p.id} className="activity-item" style={{ cursor: 'pointer' }} onClick={() => navigate(`/dashboard/${p.id}`)}>
                  <div className="activity-main">
                    <div className="doc-icon"><Icon name="description" /></div>
                    <div>
                      <strong>{p.numero_processo}</strong>
                      <p className="muted" style={{ fontSize: '0.8rem' }}>Added {new Date(p.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className={`status-pill ${p.status === 'concluido' ? 'success' : 'warning'}`}>{p.status}</span>
                    <Icon name="chevron_right" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    );
  }

  // ── Analysis detail logic ─────────────────────────────────────────────────
  if (loadingAnalysis) {
    return (
      <main className="screen dashboard-screen">
        <div className="panel panel-inner" style={{ padding: '2rem', textAlign: 'center' }}>
          <div className="mini-icon upload-screen__pulse-icon" style={{ margin: '0 auto 1rem' }}><Icon name="auto_awesome" /></div>
          <p className="lede">Loading AI analysis…</p>
        </div>
      </main>
    );
  }

  if (analysisError || !analise) {
    return (
      <main className="screen dashboard-screen">
        <div className="panel panel-inner" style={{ padding: '2rem', textAlign: 'center' }}>
          <p className="lede" style={{ marginTop: 12 }}>Analysis not ready yet.</p>
          <p className="muted">The AI pipeline may still be processing. Trigger it manually or wait.</p>
          <button className="primary-button" style={{ marginTop: 16 }} onClick={handleTriggerAnalysis} disabled={analyze.isPending}>
            {analyze.isPending ? 'Triggering…' : 'Run AI Analysis'}
          </button>
        </div>
        <MetadataPanel meta={processo?.metadata_extraida} />
      </main>
    );
  }

  const isAcordo = analise.decisao === 'ACORDO';
  const proposta = analise.proposta;

  return (
    <main className="screen dashboard-screen">
      <div className="hero-grid dashboard-screen__grid">
        <section className="panel panel-inner hero-banner dashboard-screen__hero">
          <div className="title-kicker">AI Analysis Outcome</div>
          <h1 className="headline dashboard-screen__headline">
            Recommended Action:{' '}
            <span className="accent">{isAcordo ? 'Settlement' : 'Defense'}</span>
          </h1>
          <p className="lede dashboard-screen__lede">{analise.rationale}</p>

          <div style={{ marginBottom: 8 }}>
            <ConfidenceBadge value={analise.confidence} />
            {analise.requires_supervisor && (
              <span style={{ marginLeft: 12, color: 'var(--danger)', fontWeight: 700, fontSize: '0.85rem' }}>
                ⚠ Supervisor review required
              </span>
            )}
          </div>

          {proposta && (
            <div className="split-grid dashboard-screen__split" style={{ marginTop: 20 }}>
              <div className="metric-card">
                <div className="metric-label">Suggested Settlement</div>
                <h3 className="metric-value" style={{ fontSize: '1.9rem' }}>
                  <span style={{ color: 'var(--primary)' }}>{BRL(Number(proposta.valor_sugerido))}</span>
                </h3>
                <div className="metric-note">
                  <Icon name="trending_down" /> Range: {BRL(Number(proposta.intervalo_min))} – {BRL(Number(proposta.intervalo_max))}
                </div>
                <div className="muted" style={{ fontSize: '0.8rem', marginTop: 4 }}>
                  Based on {proposta.n_casos_similares} similar cases
                </div>
              </div>
              <div className="metric-card dashboard-screen__cost-card">
                <div className="section-heading" style={{ marginBottom: 10 }}>
                  <span className="metric-label">Potential Litigation Cost</span>
                  <strong>{BRL(Number(proposta.custo_estimado_litigar))}</strong>
                </div>
                <div className="progress">
                  <span style={{ width: `${Math.round((Number(proposta.valor_sugerido) / Number(proposta.custo_estimado_litigar)) * 100)}%` }} />
                </div>
                <p className="muted dashboard-screen__cost-copy">
                  Expected savings: <strong style={{ color: 'var(--success)' }}>{BRL(Number(proposta.economia_esperada))}</strong>
                </p>
              </div>
            </div>
          )}

          {!decided ? (
            <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
              {isAcordo && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <div>
                    <label className="field-label" style={{ display: 'block', marginBottom: 4 }}>Adjust value (R$)</label>
                    <input className="text-input" type="number" placeholder={String(proposta?.valor_sugerido ?? '')}
                      value={valorAjuste} onChange={(e) => setValorAjuste(e.target.value)} />
                  </div>
                  <div>
                    <label className="field-label" style={{ display: 'block', marginBottom: 4 }}>Justificativa</label>
                    <input className="text-input" type="text" placeholder="Motivo da divergência…"
                      value={justificativa} onChange={(e) => setJustificativa(e.target.value)} />
                  </div>
                </div>
              )}
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="primary-button" onClick={() => handleDecision('ACEITAR')} disabled={registerDecision.isPending}>
                  <Icon name="check_circle" /> Accept
                </button>
                {isAcordo && (
                  <button className="ghost-button" onClick={() => handleDecision('AJUSTAR')} disabled={registerDecision.isPending}>
                    <Icon name="edit" /> Adjust
                  </button>
                )}
                <button className="ghost-button" style={{ color: 'var(--danger)' }} onClick={() => handleDecision('RECUSAR')} disabled={registerDecision.isPending}>
                  <Icon name="cancel" /> Refuse / Defend
                </button>
              </div>
            </div>
          ) : (
            <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(0,128,0,0.08)', borderRadius: 8 }}>
              <Icon name="check_circle" style={{ color: 'var(--success)' }} /> Decision recorded successfully.
            </div>
          )}
        </section>

        <aside className="panel panel-inner dashboard-screen__aside">
          <div className="section-heading">
            <h3 className="section-title">Analyzed Documents</h3>
            <Icon name="filter_list" />
          </div>

          {analise.trechos_chave.length > 0 ? (
            <div className="doc-list">
              {analise.trechos_chave.map((t, i) => (
                <div key={i} className="doc-item">
                  <div className="doc-main">
                    <div className="doc-icon"><Icon name="description" /></div>
                    <div>
                      <strong style={{ fontSize: '0.82rem' }}>{t.doc} p.{t.page}</strong>
                      <p className="muted" style={{ fontSize: '0.78rem', marginTop: 2 }}>"{t.quote}"</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="doc-list">
              {dashboardDocs.map((doc) => (
                <div key={doc.name} className="doc-item">
                  <div className="doc-main">
                    <div className="doc-icon"><Icon name={doc.icon} /></div>
                    <strong>{doc.name}</strong>
                  </div>
                  <span className={`status-pill ${doc.tone ?? 'success'}`}>{doc.status}</span>
                </div>
              ))}
            </div>
          )}

          <div style={{ marginTop: 18 }}>
            <div className="field-label" style={{ marginBottom: 8 }}>Factors</div>
            {analise.fatores_pro_acordo.map((f, i) => (
              <div key={i} className="muted" style={{ fontSize: '0.8rem', marginBottom: 4 }}>
                <Icon name="arrow_forward" style={{ fontSize: '0.9rem', color: 'var(--success)' }} /> {f}
              </div>
            ))}
            {analise.fatores_pro_defesa.map((f, i) => (
              <div key={i} className="muted" style={{ fontSize: '0.8rem', marginBottom: 4 }}>
                <Icon name="arrow_forward" style={{ fontSize: '0.9rem', color: 'var(--danger)' }} /> {f}
              </div>
            ))}
          </div>
        </aside>
      </div>

      <MetadataPanel meta={processo?.metadata_extraida} />

      <section className="panel panel-inner dashboard-screen__risk" style={{ marginTop: 24 }}>
        <div className="section-heading">
          <h3 className="section-title">Advanced Risk Indicators</h3>
          <button type="button" className="ghost-button" onClick={() => navigate('/monitoring')}>
            Open Monitoring
          </button>
        </div>
        <div className="insight-grid dashboard-screen__rings">
          {riskIndicators.map((indicator) => (
            <div key={indicator.label} style={{ textAlign: 'center' }}>
              <div className="ring-wrap">
                <svg className="ring" viewBox="0 0 132 132" width="132" height="132">
                  <circle cx="66" cy="66" r="58" fill="none" stroke="rgba(91,67,52,0.12)" strokeWidth="8" />
                  <circle cx="66" cy="66" r="58" fill="none"
                    stroke={indicator.color === 'danger' ? '#ba1a1a' : indicator.color === 'tertiary' ? '#00658f' : '#904d00'}
                    strokeWidth="8" strokeLinecap="round" strokeDasharray="364.4"
                    strokeDashoffset={364.4 - (364.4 * indicator.value) / 100}
                    transform="rotate(-90 66 66)" />
                </svg>
                <span className="ring-value">{indicator.value}%</span>
              </div>
              <p className="ring-label">{indicator.label}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
