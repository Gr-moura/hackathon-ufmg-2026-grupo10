import { useNavigate } from 'react-router-dom';
import { useMetrics, useRecommendations } from '../../api/metrics';
import { Icon } from '../../modules/ui/Icon';
import { statsCards } from '../../data';
import './MonitoringScreen.css';

const BRL = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const PCT = (v: number) => `${Math.round(v * 100)}%`;

export function MonitoringScreen() {
  const navigate = useNavigate();
  const { data: metrics, isLoading: metricsLoading } = useMetrics();
  const { data: recommendations, isLoading: recsLoading } = useRecommendations();

  const liveCards = metrics
    ? [
        { label: 'Total de Decisões', value: String(metrics.total_decisoes), note: `${metrics.total_processos} processos`, icon: 'task_alt' },
        { label: 'Aderência a Acordos', value: metrics.aderencia_global != null ? PCT(metrics.aderencia_global) : '—', note: 'Dentro da meta', icon: 'verified_user' },
        { label: 'Economia Total', value: metrics.economia_total != null ? BRL(metrics.economia_total) : '—', note: 'vs. custo de litígio', icon: 'payments' },
        { label: 'Casos de Alto Risco', value: String(metrics.casos_alto_risco), note: 'Confiança < 60%', icon: 'warning' },
      ]
    : statsCards;

  return (
    <main className="screen monitoring-screen">
      <div className="monitor-grid monitoring-screen__grid">
        <section className="panel panel-inner hero-banner monitoring-screen__hero">
          <div className="title-kicker monitoring-screen__kicker">Monitoramento Executivo</div>
          <h1 className="headline monitoring-screen__headline">
            Banco UFMG <span className="accent">Operações</span>
          </h1>
          <p className="lede monitoring-screen__lede">
            Acompanhe aderência, economia e casos de alto risco em um único painel.
          </p>

          <div className="split-grid monitoring-screen__stats" style={{ marginTop: 28 }}>
            {liveCards.map((card, index) => (
              <article key={card.label} className={`metric-card monitoring-screen__stat-card ${index === 3 ? 'monitoring-screen__stat-card--accent' : ''}`}>
                <div className="section-heading" style={{ marginBottom: 10 }}>
                  <Icon name={card.icon} className={index === 3 ? 'monitoring-screen__stat-icon monitoring-screen__stat-icon--accent' : 'monitoring-screen__stat-icon'} />
                  <span className={`mini-pill monitoring-screen__note ${index === 3 ? 'monitoring-screen__note--accent' : ''}`}>{card.note}</span>
                </div>
                <div className={`metric-label ${index === 3 ? 'monitoring-screen__stat-label--accent' : ''}`}>{card.label}</div>
                <div className="metric-value monitoring-screen__stat-value">
                  {metricsLoading ? '…' : card.value}
                </div>
              </article>
            ))}
          </div>
        </section>

        <aside className="panel panel-inner monitoring-screen__feed-column">
          <div className="section-heading">
            <div>
              <h3 className="section-title-strong monitoring-screen__feed-title">Recomendações da IA</h3>
              <p className="section-text monitoring-screen__feed-subtitle">Feed em tempo real de alinhamento com a política</p>
            </div>
            <button type="button" className="ghost-button" onClick={() => navigate('/processes')}>
              Abrir Mesa de Decisão
            </button>
          </div>

          <div className="feed-list">
            {recsLoading && <p className="muted">Carregando feed…</p>}
            {recommendations && recommendations.length === 0 && (
              <p className="muted">Nenhuma recomendação ainda. Envie casos para começar.</p>
            )}
            {recommendations?.map((rec) => {
              const tone = rec.decisao === 'ACORDO' ? 'success' : 'neutral';
              const confPct = Math.round(rec.confidence * 100);
              return (
                <article
                  key={rec.processo_id}
                  className="feed-item monitoring-screen__feed-item"
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/dashboard/${rec.processo_id}`)}
                >
                  <div className="feed-main monitoring-screen__feed-main">
                    <div>
                      <div className={`rec-title ${tone}`}>{rec.decisao === 'ACORDO' ? 'Proposta de acordo' : 'Estratégia de defesa'}</div>
                      <h4 className="section-title-strong monitoring-screen__case-title">{rec.numero_processo}</h4>
                      <p className="card-text monitoring-screen__feed-copy">
                        {rec.valor_sugerido != null ? `Sugerido ${BRL(rec.valor_sugerido)}` : 'Defesa recomendada — sem valor de acordo.'}
                      </p>
                    </div>
                  </div>
                  <div className="monitoring-screen__meta">
                    <div className="muted monitoring-screen__time">
                      {new Date(rec.created_at).toLocaleString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <span className={`tag ${confPct >= 85 ? 'success' : confPct >= 60 ? 'warning' : 'danger'}`}>
                      {confPct}% de match
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        </aside>
      </div>

      <section className="panel panel-inner monitoring-screen__table-panel" style={{ marginTop: 24 }}>
        <div className="section-heading">
          <h3 className="section-title-strong monitoring-screen__table-title">Matriz de aderência por advogado</h3>
          <button type="button" className="ghost-button">Exportar relatório completo</button>
        </div>

        <div className="table-wrap">
          <table className="data-table monitoring-screen__table">
            <thead>
              <tr>
                <th>ID do advogado</th>
                <th>Total de decisões</th>
                <th>Índice de aderência</th>
                <th>Aceitas</th>
              </tr>
            </thead>
            <tbody>
              {metricsLoading && (
                <tr><td colSpan={4} style={{ textAlign: 'center' }} className="muted">Carregando…</td></tr>
              )}
              {metrics?.aderencia_por_advogado.length === 0 && !metricsLoading && (
                <tr><td colSpan={4} style={{ textAlign: 'center' }} className="muted">Nenhuma decisão registrada ainda.</td></tr>
              )}
              {metrics?.aderencia_por_advogado.map((row) => (
                <tr key={row.advogado_id}>
                  <td><div className="row-head"><div className="avatar">{row.advogado_id.slice(0, 2).toUpperCase()}</div><div className="muted" style={{ fontSize: '0.78rem' }}>{row.advogado_id.slice(0, 8)}…</div></div></td>
                  <td>{row.total}</td>
                  <td>
                    <div className="row-head" style={{ gap: 10 }}>
                      <div className="bar"><span style={{ width: `${Math.round(row.aderencia * 100)}%` }} /></div>
                      <strong>{Math.round(row.aderencia * 100)}%</strong>
                    </div>
                  </td>
                  <td>{row.aceitos} / {row.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
