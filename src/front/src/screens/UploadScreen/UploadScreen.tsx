import { recentFiles, uploadCategories } from '../../data';
import { Icon } from '../../modules/ui/Icon';
import './UploadScreen.css';

export function UploadScreen({ onOpenDashboard }: { onOpenDashboard: () => void }) {
  return (
    <main className="screen upload-screen">
      <section className="panel panel-inner upload-screen__summary">
        <div className="section-heading upload-screen__heading">
          <div>
            <h1 className="section-title-strong upload-screen__title">Evidence Hub</h1>
            <p className="section-text upload-screen__subtitle">Centralize and process legal documentation for automated adherence analysis.</p>
          </div>
          <button type="button" className="ghost-button" onClick={onOpenDashboard}>
            Return to Decision Lab
          </button>
        </div>

        <div className="metric-card upload-screen__progress-card">
          <div className="section-heading upload-screen__progress-heading">
            <div className="doc-main upload-screen__analyzing-copy">
              <div className="mini-icon upload-screen__pulse-icon">
                <Icon name="auto_awesome" />
              </div>
              <div>
                <h3 className="section-title-strong upload-screen__progress-title">AI Analyzing Evidence...</h3>
                <p className="section-text upload-screen__progress-subtitle">Cross-referencing lawsuit 2024.089.12 with internal bank policies.</p>
              </div>
            </div>
            <strong className="upload-screen__progress-value">64%</strong>
          </div>
          <div className="progress">
            <span style={{ width: '64%' }} />
          </div>
        </div>
      </section>

      <div className="upload-grid upload-screen__grid">
        <section className="panel panel-inner upload-screen__drop-column">
          <div className="section-heading">
            <span className="section-title">Destination: Legal Folder</span>
          </div>
          <div className="upload-zone upload-screen__drop-zone">
            <div>
              <div className="upload-icon upload-screen__drop-icon">
                <Icon name="upload_file" style={{ fontSize: '2.4rem' }} />
              </div>
              <h2 className="section-title-strong upload-screen__drop-title">Process Autos</h2>
              <p className="section-text upload-screen__drop-copy">Drop the full lawsuit PDF or historical case files here.</p>
              <button className="primary-button" type="button">
                Browse Files
              </button>
            </div>
          </div>
        </section>

        <section className="panel panel-inner upload-screen__evidence-column">
          <div className="section-heading">
            <span className="section-title">Internal Subsídios</span>
          </div>
          <div className="upload-zone dashed upload-screen__subsidiary-zone">
            <div>
              <div className="doc-main upload-screen__badges-row">
                <div className="avatar upload-screen__badge"> <Icon name="contract" /> </div>
                <div className="avatar upload-screen__badge upload-screen__badge--warm"><Icon name="receipt_long" /></div>
                <div className="avatar upload-screen__badge upload-screen__badge--cool"><Icon name="payments" /></div>
              </div>
              <h2 className="section-title-strong upload-screen__evidence-title">Bank Evidence</h2>
              <p className="section-text upload-screen__evidence-copy">Upload internal proofs & subsidies.</p>
              <div className="upload-screen__file-tags">
                <span className="mini-pill">PDF</span>
                <span className="mini-pill">XLSX</span>
                <span className="mini-pill">PNG</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section className="panel panel-inner upload-screen__categories" style={{ marginTop: 24 }}>
        <div className="section-heading">
          <h3 className="section-title">Document Categories</h3>
          <span className="muted" style={{ fontSize: '0.82rem' }}>Bento grid intake</span>
        </div>
        <div className="upload-screen__category-grid">
          {uploadCategories.map((category) => (
            <article key={category.title} className="category-card upload-screen__category-card">
              <div>
                <div className="doc-icon upload-screen__category-icon">
                  <Icon name={category.icon} />
                </div>
                <h4 className="section-title-strong upload-screen__category-title">{category.title}</h4>
                <p className="card-text upload-screen__category-copy">{category.description}</p>
              </div>
              <span className="tag success">{category.tag}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="panel panel-inner upload-screen__recent" style={{ marginTop: 24 }}>
        <div className="section-heading">
          <h3 className="section-title">Recently Processed</h3>
          <button type="button" className="ghost-button" onClick={onOpenDashboard}>
            Compare with decision output
          </button>
        </div>
        <div className="activity-list">
          {recentFiles.map((file) => (
            <div key={file.name} className="activity-item upload-screen__recent-item">
              <div className="activity-main">
                <div className="doc-icon">
                  <Icon name="picture_as_pdf" />
                </div>
                <div>
                  <strong>{file.name}</strong>
                  <p className="muted upload-screen__recent-meta">{file.time} • {file.size}</p>
                </div>
              </div>
              <span className={`status-pill ${file.tone === 'danger' ? 'danger' : 'success'}`}>{file.status}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}