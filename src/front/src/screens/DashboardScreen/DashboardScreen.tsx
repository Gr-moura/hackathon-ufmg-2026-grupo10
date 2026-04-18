import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAnalysis, useProcesso, useRegisterDecision, useAnalyzeProcesso } from '../../api/processes';
import { Icon } from '../../modules/ui/Icon';
import type { AcaoAdvogado } from '../../api/types';
import './DashboardScreen.css';

const DOC_TYPE_LABELS: Record<string, { label: string; icon: string }> = {
  PETICAO_INICIAL: { label: 'Petição Inicial', icon: 'gavel' },
  PROCURACAO: { label: 'Procuração', icon: 'badge' },
  CONTRATO: { label: 'Contrato', icon: 'description' },
  EXTRATO: { label: 'Extrato', icon: 'receipt_long' },
  COMPROVANTE_CREDITO: { label: 'Comprovante de Crédito', icon: 'payments' },
  DOSSIE: { label: 'Dossiê', icon: 'folder_open' },
  DEMONSTRATIVO_DIVIDA: { label: 'Demonstrativo de Dívida', icon: 'trending_up' },
  LAUDO_REFERENCIADO: { label: 'Laudo Referenciado', icon: 'lab_profile' },
  OUTRO: { label: 'Outro', icon: 'attach_file' },
};

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

interface RingProps { value: number; label: string; color: string; }
function ConfidenceRing({ value, label, color }: RingProps) {
  const pct = Math.round(value * 100);
  const circumference = 364.4;
  const offset = circumference - (circumference * pct) / 100;
  return (
    <div style={{ textAlign: 'center' }}>
      <div className="ring-wrap">
        <svg className="ring" viewBox="0 0 132 132" width="132" height="132">
          <circle cx="66" cy="66" r="58" fill="none" stroke="rgba(91,67,52,0.12)" strokeWidth="8" />
          <circle
            cx="66" cy="66" r="58"
            fill="none" stroke={color} strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 66 66)"
          />
        </svg>
        <span className="ring-value">{pct}%</span>
      </div>
      <p className="ring-label">{label}</p>
    </div>
  );
}

export function DashboardScreen() {
  const { processoId } = useParams<{ processoId: string }>();
  const navigate = useNavigate();

  const [adjusting, setAdjusting] = useState(false);
  const [adjustValue, setAdjustValue] = useState('');
  const [adjustJustif, setAdjustJustif] = useState('');
  const [decided, setDecided] = useState(false);

  const { data: analysis, isLoading, isError } = useAnalysis(processoId);
  const { data: processo } = useProcesso(processoId);
  const registerDecision = useRegisterDecision();
  const analyze = useAnalyzeProcesso();

  async function handleDecision(acao: AcaoAdvogado, valor?: number, justif?: string) {
    if (!analysis) return;
    await registerDecision.mutateAsync({
      analiseId: analysis.id,
      acao,
      valor_advogado: valor ?? null,
      justificativa: justif ?? null,
    });
    setDecided(true);
    setAdjusting(false);
  }

  async function handleRunAnalysis() {
    if (!processoId) return;
    await analyze.mutateAsync(processoId);
  }

  // No process selected
  if (!processoId) {
    return (
      <main className="screen dashboard-screen">
        <div className="panel panel-inner" style={{ padding: 40, textAlign: 'center' }}>
          <p className="muted">
            Nenhum processo selecionado.{' '}
            <button className="ghost-button" onClick={() => navigate('/upload')}>
Ir para Central de Evidências
            </button>
          </p>
        </div>
      </main>
    );
  }

  // Loading
  if (isLoading) {
    return (
      <main className="screen dashboard-screen">
        <div className="panel panel-inner" style={{ padding: 40, textAlign: 'center' }}>
          <div className="doc-main" style={{ justifyContent: 'center', gap: 12 }}>
            <div className="mini-icon"><Icon name="auto_awesome" /></div>
            <p className="section-title-strong">Carregando análise…</p>
          </div>
        </div>
      </main>
    );
  }

  // No analysis yet (404) — offer to run
  if (isError || !analysis) {
    return (
      <main className="screen dashboard-screen">
        <div className="panel panel-inner" style={{ padding: 40, textAlign: 'center' }}>
          <p className="section-title-strong" style={{ marginBottom: 12 }}>Análise não encontrada</p>
          <p className="muted" style={{ marginBottom: 20 }}>
            O pipeline de IA ainda não foi executado para este processo.
          </p>
          <button
            className="primary-button"
            onClick={handleRunAnalysis}
            disabled={analyze.isPending}
          >
            {analyze.isPending ? 'Analisando…' : 'Executar análise de IA'}
          </button>
          {analyze.isError && (
            <p style={{ color: 'var(--danger)', marginTop: 12, fontSize: '0.85rem' }}>
              Falha ao executar análise. Verifique os logs do servidor.
            </p>
          )}
        </div>
      </main>
    );
  }

  const isAcordo = analysis.decisao === 'ACORDO';
  const confidencePct = Math.round(analysis.confidence * 100);
  const accentColor = isAcordo ? 'var(--primary)' : '#2e7d32';

  return (
    <main className="screen dashboard-screen">
      <div className="hero-grid dashboard-screen__grid">

        {/* ── Painel principal — recomendação ── */}
        <section className="panel panel-inner hero-banner dashboard-screen__hero">
          <div className="title-kicker">Resultado da análise de IA</div>
          <h1 className="headline dashboard-screen__headline">
            Recomendação:{' '}
            <span style={{ color: accentColor }}>
              {isAcordo ? 'Acordo' : 'Defesa'}
            </span>
          </h1>

          {analysis.requires_supervisor && (
            <div className="glass-card" style={{ marginTop: 12, padding: '10px 16px', display: 'flex', gap: 8, alignItems: 'center' }}>
              <Icon name="warning" />
              <span style={{ fontSize: '0.85rem' }}>
                Confiança intermediária — recomenda-se revisão supervisora antes de decidir.
              </span>
            </div>
          )}

          <p className="lede dashboard-screen__lede" style={{ marginTop: 14 }}>
            {analysis.rationale.split('\n\n')[0]}
          </p>

          {/* Valores (ACORDO) */}
          {isAcordo && analysis.proposta ? (
            <div className="split-grid dashboard-screen__split" style={{ marginTop: 28 }}>
              <div className="metric-card">
                <div className="metric-label">Proposta de Acordo</div>
                <h3 className="metric-value" style={{ fontSize: '1.9rem' }}>
                  <span style={{ color: 'var(--primary)' }}>
                    {formatBRL(analysis.proposta.valor_sugerido)}
                  </span>
                </h3>
                <p className="metric-note">
                  Intervalo: {formatBRL(analysis.proposta.intervalo_min)} –{' '}
                  {formatBRL(analysis.proposta.intervalo_max)}
                </p>
              </div>

              <div className="metric-card dashboard-screen__cost-card">
                <div className="section-heading" style={{ marginBottom: 10 }}>
                  <span className="metric-label">Custo estimado de litigar</span>
                  <strong>{formatBRL(analysis.proposta.custo_estimado_litigar)}</strong>
                </div>
                <div className="progress">
                  <span
                    style={{
                      width: `${Math.min(
                        (analysis.proposta.valor_sugerido / analysis.proposta.custo_estimado_litigar) * 100,
                        100,
                      ).toFixed(0)}%`,
                    }}
                  />
                </div>
                <p className="muted dashboard-screen__cost-copy">
                  Economia esperada:{' '}
                  <strong>{formatBRL(analysis.proposta.economia_esperada)}</strong>{' '}
                  ao optar pelo acordo.
                </p>
              </div>
            </div>
          ) : !isAcordo ? (
            <div className="metric-card" style={{ marginTop: 28, display: 'flex', gap: 16, alignItems: 'center' }}>
              <div>
                <div className="metric-label">Confiança na defesa</div>
                <h3 className="metric-value">{confidencePct}%</h3>
              </div>
              <div style={{ flex: 1 }}>
                <div className="progress">
                  <span style={{ width: `${confidencePct}%` }} />
                </div>
              </div>
            </div>
          ) : null}

          {/* ── Botões HITL ── */}
          {decided ? (
            <div className="glass-card" style={{ marginTop: 28, padding: '14px 18px', display: 'flex', gap: 10, alignItems: 'center' }}>
              <Icon name="check_circle" />
              <span style={{ fontWeight: 600 }}>Decisão registrada com sucesso.</span>
              <button className="ghost-button" style={{ marginLeft: 'auto' }} onClick={() => navigate('/monitoring')}>
                Ver monitoramento
              </button>
            </div>
          ) : adjusting ? (
            <div className="glass-card" style={{ marginTop: 28, padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <p className="section-title-strong" style={{ margin: 0 }}>Ajustar proposta</p>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 160 }}>
                  <label className="metric-label" htmlFor="adjust-value">Valor (R$)</label>
                  <input
                    id="adjust-value"
                    type="number"
                    min={0}
                    step={100}
                    value={adjustValue}
                    onChange={(e) => setAdjustValue(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--outline)', background: 'var(--surface)', color: 'var(--on_surface)', fontSize: '0.95rem' }}
                    placeholder="Ex: 4500"
                  />
                </div>
                <div style={{ flex: 2, minWidth: 200 }}>
                  <label className="metric-label" htmlFor="adjust-justif">Justificativa</label>
                  <input
                    id="adjust-justif"
                    type="text"
                    value={adjustJustif}
                    onChange={(e) => setAdjustJustif(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--outline)', background: 'var(--surface)', color: 'var(--on_surface)', fontSize: '0.95rem' }}
                    placeholder="Motivo do ajuste…"
                  />
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  className="primary-button"
                  disabled={registerDecision.isPending || !adjustValue}
                  onClick={() => handleDecision('AJUSTAR', Number(adjustValue), adjustJustif || undefined)}
                >
                  {registerDecision.isPending ? 'Salvando…' : 'Confirmar ajuste'}
                </button>
                <button className="ghost-button" onClick={() => setAdjusting(false)}>Cancelar</button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 10, marginTop: 28, flexWrap: 'wrap' }}>
              <button
                className="primary-button"
                disabled={registerDecision.isPending}
                onClick={() => handleDecision('ACEITAR')}
              >
                <Icon name="check" /> Aceitar recomendação
              </button>
              {isAcordo && (
                <button
                  className="ghost-button"
                  disabled={registerDecision.isPending}
                  onClick={() => setAdjusting(true)}
                >
                  <Icon name="edit" /> Ajustar valor
                </button>
              )}
              <button
                className="ghost-button"
                disabled={registerDecision.isPending}
                onClick={() => handleDecision('RECUSAR', undefined, 'Advogado optou por defender.')}
                style={{ color: 'var(--error, #ba1a1a)' }}
              >
                <Icon name="close" /> {isAcordo ? 'Recusar — defender' : 'Recusar — propor acordo'}
              </button>
            </div>
          )}
        </section>

        {/* ── Sidebar documentos ── */}
        <aside className="panel panel-inner dashboard-screen__aside">
          <div className="section-heading">
            <h3 className="section-title">Documentos Analisados</h3>
            <Icon name="filter_list" />
          </div>
          <div className="doc-list">
            {processo?.documentos.map((doc) => {
              const meta = DOC_TYPE_LABELS[doc.doc_type] ?? DOC_TYPE_LABELS.OUTRO;
              const hasErrors = doc.parse_errors && doc.parse_errors.length > 0;
              return (
                <div key={doc.id} className="doc-item">
                  <div className="doc-main">
                    <div className="doc-icon"><Icon name={meta.icon} /></div>
                    <div>
                      <strong style={{ fontSize: '0.85rem' }}>{meta.label}</strong>
                      <p className="muted" style={{ fontSize: '0.75rem', margin: 0 }}>{doc.original_filename}</p>
                    </div>
                  </div>
                  <span className={`status-pill ${hasErrors ? 'warning' : 'success'}`}>
                    {hasErrors ? 'Parcial' : 'OK'}
                  </span>
                </div>
              );
            })}
            {(!processo?.documentos || processo.documentos.length === 0) && (
              <p className="muted" style={{ fontSize: '0.82rem' }}>Sem documentos registrados.</p>
            )}
          </div>

          <div className="glass-card dashboard-screen__audit" style={{ marginTop: 18 }}>
            <div className="section-heading" style={{ marginBottom: 8 }}>
              <div className="doc-main" style={{ gap: 10 }}>
                <Icon name="info" />
                <h4 className="section-title-strong" style={{ fontSize: '0.9rem' }}>Detalhes do processo</h4>
              </div>
            </div>
            <p className="muted" style={{ margin: 0, fontSize: '0.82rem', lineHeight: 1.7 }}>
              Nº {processo?.numero_processo ?? '—'}<br />
              Status: <strong style={{ color: 'var(--primary)' }}>{processo?.status ?? '—'}</strong><br />
              UF: {processo?.metadata_extraida?.uf ?? '—'} ·{' '}
              {processo?.metadata_extraida?.valor_da_causa
                ? formatBRL(processo.metadata_extraida.valor_da_causa)
                : 'Valor N/A'}
            </p>
          </div>
        </aside>
      </div>

      {/* ── Fatores de risco / fortalezas ── */}
      <section className="panel panel-inner dashboard-screen__risk" style={{ marginTop: 24 }}>
        <div className="section-heading">
          <h3 className="section-title">Fatores da Análise</h3>
          <button type="button" className="ghost-button" onClick={() => navigate('/monitoring')}>
            Ver monitoramento
          </button>
        </div>

        <div className="insight-grid dashboard-screen__rings" style={{ alignItems: 'start', gridTemplateColumns: '1fr 1fr auto' }}>
          {/* Pró-acordo */}
          <div>
            <p className="metric-label" style={{ marginBottom: 10, color: 'var(--primary)' }}>
              <Icon name="warning" /> Fatores pró-acordo
            </p>
            {analysis.fatores_pro_acordo.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {analysis.fatores_pro_acordo.map((f, i) => (
                  <li key={i} className="muted" style={{ fontSize: '0.85rem', marginBottom: 4 }}>{f}</li>
                ))}
              </ul>
            ) : (
              <p className="muted" style={{ fontSize: '0.85rem' }}>Nenhum fator identificado.</p>
            )}
          </div>

          {/* Pró-defesa */}
          <div>
            <p className="metric-label" style={{ marginBottom: 10, color: accentColor }}>
              <Icon name="shield" /> Fatores pró-defesa
            </p>
            {analysis.fatores_pro_defesa.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {analysis.fatores_pro_defesa.map((f, i) => (
                  <li key={i} className="muted" style={{ fontSize: '0.85rem', marginBottom: 4 }}>{f}</li>
                ))}
              </ul>
            ) : (
              <p className="muted" style={{ fontSize: '0.85rem' }}>Nenhum fator identificado.</p>
            )}
          </div>

          {/* Ring de confiança */}
          <ConfidenceRing
            value={analysis.confidence}
            label="Confiança IA"
            color={analysis.confidence >= 0.85 ? '#2e7d32' : analysis.confidence >= 0.60 ? '#904d00' : '#ba1a1a'}
          />
        </div>
      </section>
    </main>
  );
}
