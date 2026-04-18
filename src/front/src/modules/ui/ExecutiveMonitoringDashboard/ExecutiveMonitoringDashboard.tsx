import { useMetrics } from '../../../api/metrics';
import { Icon } from '../Icon';
import './ExecutiveMonitoringDashboard.css';

const BRL = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const PCT = (v: number) => `${Math.round(v * 100)}%`;

export function ExecutiveMonitoringDashboard({ className = '' }: { className?: string }) {
  const { data: metrics, isLoading } = useMetrics();

  const statsCards = metrics
    ? [
        {
          label: 'Total de Decisões',
          value: String(metrics.total_decisoes),
          note: `${metrics.total_processos} processos`,
          icon: 'task_alt',
        },
        {
          label: 'Aderência a Acordos',
          value: metrics.aderencia_global != null ? PCT(metrics.aderencia_global) : '—',
          note: 'Dentro da meta',
          icon: 'verified_user',
        },
        {
          label: 'Economia Total',
          value: metrics.economia_total != null ? BRL(metrics.economia_total) : '—',
          note: 'vs. custo de litígio',
          icon: 'payments',
        },
        {
          label: 'Casos de Alto Risco',
          value: String(metrics.casos_alto_risco),
          note: 'Confiança < 60%',
          icon: 'warning',
        },
      ]
    : [
        { label: 'Total de Decisões', value: '—', note: '— processos', icon: 'task_alt' },
        { label: 'Aderência a Acordos', value: '—', note: 'Dentro da meta', icon: 'verified_user' },
        { label: 'Economia Total', value: '—', note: 'vs. custo de litígio', icon: 'payments' },
        { label: 'Casos de Alto Risco', value: '—', note: 'Confiança < 60%', icon: 'warning' },
      ];

  return (
    <section className={`panel panel-inner hero-banner executive-monitoring-dashboard ${className}`.trim()}>
      <div className="title-kicker executive-monitoring-dashboard__kicker">Monitoramento Executivo</div>
      <h2 className="headline executive-monitoring-dashboard__headline">
        Banco UFMG <span className="accent">Operações</span>
      </h2>
      <p className="lede executive-monitoring-dashboard__lede">
        Acompanhe aderência, economia e casos de alto risco em um único painel. Use os dados para avaliar
        se a política de acordos está funcionando.
      </p>

      <div className="split-grid executive-monitoring-dashboard__stats">
        {statsCards.map((card, index) => (
          <article
            key={card.label}
            className={`metric-card executive-monitoring-dashboard__stat-card ${index === 3 ? 'executive-monitoring-dashboard__stat-card--accent' : ''}`}
          >
            <div className="section-heading executive-monitoring-dashboard__stat-head">
              <Icon
                name={card.icon}
                className={
                  index === 3
                    ? 'executive-monitoring-dashboard__stat-icon executive-monitoring-dashboard__stat-icon--accent'
                    : 'executive-monitoring-dashboard__stat-icon'
                }
              />
              <span
                className={`mini-pill executive-monitoring-dashboard__note ${index === 3 ? 'executive-monitoring-dashboard__note--accent' : ''}`}
              >
                {card.note}
              </span>
            </div>
            <div
              className={`metric-label ${index === 3 ? 'executive-monitoring-dashboard__stat-label--accent' : ''}`}
            >
              {card.label}
            </div>
            <div className="metric-value executive-monitoring-dashboard__stat-value">
              {isLoading ? '…' : card.value}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
