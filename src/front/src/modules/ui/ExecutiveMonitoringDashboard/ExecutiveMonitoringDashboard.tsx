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
          label: 'Total Decisions',
          value: String(metrics.total_decisoes),
          note: `${metrics.total_processos} processos`,
          icon: 'task_alt',
        },
        {
          label: 'Settlement Adherence',
          value: metrics.aderencia_global != null ? PCT(metrics.aderencia_global) : '—',
          note: 'On Target',
          icon: 'verified_user',
        },
        {
          label: 'Total Savings',
          value: metrics.economia_total != null ? BRL(metrics.economia_total) : '—',
          note: 'vs litigation cost',
          icon: 'payments',
        },
        {
          label: 'High-Risk Cases',
          value: String(metrics.casos_alto_risco),
          note: 'Confidence < 60%',
          icon: 'warning',
        },
      ]
    : [
        { label: 'Total Decisions', value: '—', note: '— processos', icon: 'task_alt' },
        { label: 'Settlement Adherence', value: '—', note: 'On Target', icon: 'verified_user' },
        { label: 'Total Savings', value: '—', note: 'vs litigation cost', icon: 'payments' },
        { label: 'High-Risk Cases', value: '—', note: 'Confidence < 60%', icon: 'warning' },
      ];

  return (
    <section className={`panel panel-inner hero-banner executive-monitoring-dashboard ${className}`.trim()}>
      <div className="title-kicker executive-monitoring-dashboard__kicker">Executive Monitoring</div>
      <h2 className="headline executive-monitoring-dashboard__headline">
        Bank UFMG <span className="accent">Operations</span>
      </h2>
      <p className="lede executive-monitoring-dashboard__lede">
        Track adherence, savings, and high-risk cases in one control surface. Use the data to assess
        whether the agreement policy is working.
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
