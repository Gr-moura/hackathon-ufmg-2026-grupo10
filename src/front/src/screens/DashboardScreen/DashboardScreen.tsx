import { useNavigate } from 'react-router-dom';
import { dashboardDocs, riskIndicators } from '../../data';
import { Icon } from '../../modules/ui/Icon';
import './DashboardScreen.css';

export function DashboardScreen() {
  const navigate = useNavigate();

  return (
    <main className="screen dashboard-screen">
      <div className="hero-grid dashboard-screen__grid">
        <section className="panel panel-inner hero-banner dashboard-screen__hero">
          <div className="title-kicker">AI Analysis Outcome</div>
          <h1 className="headline dashboard-screen__headline">
            Recommended Action: <span className="accent">Settlement</span>
          </h1>
          <p className="lede dashboard-screen__lede">
            Based on cross-referenced dossiers and recent judicial precedents in the UFMG regional circuit, a pre-litigation settlement is advised to minimize financial exposure and administrative overhead.
          </p>

          <div className="split-grid dashboard-screen__split">
            <div className="metric-card">
              <div className="metric-label">Calculated Threshold</div>
              <h3 className="metric-value dashboard-screen__threshold-value">
                Suggested Settlement Offer: <span className="dashboard-screen__threshold-price">R$ 5.400,00</span>
              </h3>
              <div className="metric-note">
                <Icon name="trending_down" /> -18% vs Market Average
              </div>
            </div>

            <div className="metric-card dashboard-screen__cost-card">
              <div className="section-heading dashboard-screen__cost-heading">
                <span className="metric-label">Potential Litigation Cost</span>
                <strong>R$ 12.800,00</strong>
              </div>
              <div className="progress">
                <span style={{ width: '42%' }} />
              </div>
              <p className="muted dashboard-screen__cost-copy">
                Estimated including legal fees, court costs, and average punitive damages for similar dossiers.
              </p>
            </div>
          </div>
        </section>

        <aside className="panel panel-inner dashboard-screen__aside">
          <div className="section-heading">
            <h3 className="section-title">Analyzed Documents</h3>
            <Icon name="filter_list" />
          </div>
          <div className="doc-list">
            {dashboardDocs.map((doc) => (
              <div key={doc.name} className="doc-item">
                <div className="doc-main">
                  <div className="doc-icon">
                    <Icon name={doc.icon} />
                  </div>
                  <strong>{doc.name}</strong>
                </div>
                <span className={`status-pill ${doc.tone ?? 'success'}`}>{doc.status}</span>
              </div>
            ))}
          </div>

          <div className="glass-card dashboard-screen__audit">
            <div className="section-heading dashboard-screen__audit-heading">
              <div className="doc-main dashboard-screen__audit-title-row">
                <Icon name="info" className="dashboard-screen__audit-icon" />
                <h4 className="section-title-strong dashboard-screen__audit-title">Audit Trail</h4>
              </div>
            </div>
            <p className="muted dashboard-screen__audit-copy">
              Last checked: Today at 09:42 AM <br />
              System integrity: <strong className="dashboard-screen__audit-success">OPTIMAL</strong> <br />
              Data Sources: Sisjur, External API, UFMG Legacy DB.
            </p>
          </div>
        </aside>
      </div>

      <section className="panel panel-inner dashboard-screen__risk">
        <div className="section-heading">
          <h3 className="section-title">Advanced Risk Indicators</h3>
          <button type="button" className="ghost-button" onClick={() => navigate('/monitoring')}>
            Open Monitoring
          </button>
        </div>

        <div className="insight-grid dashboard-screen__rings">
          {riskIndicators.map((indicator) => (
            <div key={indicator.label} className="dashboard-screen__ring-item">
              <div className="ring-wrap">
                <svg className="ring" viewBox="0 0 120 120" width="120" height="120">
                  <circle cx="66" cy="66" r="58" fill="none" stroke="rgba(91, 67, 52, 0.12)" strokeWidth="8" />
                  <circle
                    cx="66"
                    cy="66"
                    r="58"
                    fill="none"
                    stroke={indicator.color === 'danger' ? '#ba1a1a' : indicator.color === 'tertiary' ? '#00658f' : '#904d00'}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="364.4"
                    strokeDashoffset={364.4 - (364.4 * indicator.value) / 100}
                    transform="rotate(-90 66 66)"
                  />
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