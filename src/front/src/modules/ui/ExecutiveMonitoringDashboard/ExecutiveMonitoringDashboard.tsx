import { Icon } from '../Icon';
import './ExecutiveMonitoringDashboard.css';

export function ExecutiveMonitoringDashboard({ className = '' }: { className?: string }) {
    const statsCards = [
        { label: 'Total Decisions', value: '1,429', note: '+12% vs LY', icon: 'task_alt' },
        { label: 'Settlement Adherence', value: '94.2%', note: 'On Target', icon: 'verified_user' },
        { label: 'Total Savings', value: 'R$ 2.4M', note: 'R$ 240k Saved', icon: 'payments' },
        { label: 'High-Risk Cases', value: '42', note: 'Live Attention', icon: 'warning' },
    ];
    
  return (
    <section className={`panel panel-inner hero-banner executive-monitoring-dashboard ${className}`.trim()}>
      <div className="title-kicker executive-monitoring-dashboard__kicker">Executive Monitoring</div>
      <h2 className="headline executive-monitoring-dashboard__headline">
        Bank UFMG <span className="accent">Operations</span>
      </h2>
      <p className="lede executive-monitoring-dashboard__lede">
        Track adherence, savings, and high-risk cases in one control surface. Use the data to assess whether the agreement policy is working.
      </p>

      <div className="split-grid executive-monitoring-dashboard__stats">
        {statsCards.slice(0, 4).map((card, index) => (
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
              <span className={`mini-pill executive-monitoring-dashboard__note ${index === 3 ? 'executive-monitoring-dashboard__note--accent' : ''}`}>
                {card.note}
              </span>
            </div>
            <div className={`metric-label ${index === 3 ? 'executive-monitoring-dashboard__stat-label--accent' : ''}`}>{card.label}</div>
            <div className="metric-value executive-monitoring-dashboard__stat-value">{card.value}</div>
          </article>
        ))}
      </div>
    </section>
  );
}