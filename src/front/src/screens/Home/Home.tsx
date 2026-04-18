import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../../modules/ui/Icon';
import { ExecutiveMonitoringDashboard } from '../../modules/ui/ExecutiveMonitoringDashboard/ExecutiveMonitoringDashboard';
import type { UserRole } from '../../modules/ui/LoginRoleSelector/LoginRoleSelector';
import './Home.css';

const homeCapabilities = [
    {
        icon: 'folder_open',
        title: 'Structured Case Intake',
        description: 'Create workspaces with standardized metadata so every case begins with the same operational baseline.',
    },
    {
        icon: 'account_tree',
        title: 'Decision Workflow Orchestration',
        description: 'Coordinate handoffs between legal stages with clear checkpoints and transparent ownership.',
    },
    {
        icon: 'shield_lock',
        title: 'Governance and Traceability',
        description: 'Keep decisions, notes, and evidence paths auditable across the full lifecycle of the process.',
    },
];

const workflowSteps = [
    'Define the objective and priority for the case.',
    'Open the target module from the sidebar to continue the workflow.',
    'Track outcomes and maintain process consistency through the platform.',
];

export function Home() {
    const navigate = useNavigate();

    const userRole = useMemo<UserRole>(() => {
        const savedRole = window.localStorage.getItem('enteros-role');
        return savedRole === 'Bank Administrator' ? 'Bank Administrator' : 'Lawyer';
    }, []);

    const primaryAction =
        userRole === 'Bank Administrator'
            ? {
                    label: 'Monitoring',
                    path: '/monitoring',
                    icon: 'analytics',
                    description: 'Open the monitoring center to follow operation-level indicators.',
                }
            : {
                    label: 'New Analysis',
                    path: '/upload',
                    icon: 'playlist_add',
                    description: 'Start a new analysis flow and move the case through the platform.',
                };

    return (
        <main className="screen home-screen">
            <section className="panel panel-inner hero-banner home-screen__hero">
                <div className="title-kicker">Welcome</div>
                <h1 className="headline home-screen__headline">Legal Operations Workspace</h1>
                <p className="lede home-screen__lede">
                    A single environment to organize legal routines, keep teams aligned, and move each case through a clear operational journey.
                </p>

                <div className="home-screen__action-row">
                    <button type="button" className="primary-button home-screen__primary-action" onClick={() => navigate(primaryAction.path)}>
                        <Icon name={primaryAction.icon} />
                        {primaryAction.label}
                    </button>
                    <p className="muted home-screen__action-copy">{primaryAction.description}</p>
                </div>
            </section>

            {userRole === 'Bank Administrator' && <ExecutiveMonitoringDashboard className="home-screen__admin-monitoring" />}

            {userRole === 'Lawyer' && (
                <div className="hero-grid home-screen__grid">
                    <section className="panel panel-inner home-screen__capabilities">
                        <div className="section-heading">
                            <h3 className="section-title">Platform Capabilities</h3>
                            <Icon name="widgets" />
                        </div>

                        <div className="home-screen__capability-list">
                            {homeCapabilities.map((capability) => (
                                <article key={capability.title} className="home-screen__capability-item">
                                    <div className="doc-main home-screen__capability-main">
                                        <div className="doc-icon">
                                            <Icon name={capability.icon} />
                                        </div>
                                        <div>
                                            <h4 className="section-title-strong home-screen__capability-title">{capability.title}</h4>
                                            <p className="card-text home-screen__capability-copy">{capability.description}</p>
                                        </div>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </section>

                    <aside className="panel panel-inner home-screen__flow">
                        <div className="section-heading">
                            <h3 className="section-title">Daily Flow</h3>
                            <Icon name="event_note" />
                        </div>

                        <ol className="home-screen__steps">
                            {workflowSteps.map((step) => (
                                <li key={step} className="home-screen__step-item">
                                    <p className="home-screen__step-text">{step}</p>
                                </li>
                            ))}
                        </ol>

                        <div className="glass-card home-screen__support-card">
                            <h4 className="section-title-strong home-screen__support-title">Navigation Tip</h4>
                            <p className="muted home-screen__support-copy">
                                Use the sidebar at any time to switch modules. EnterOS keeps the operational context consistent as you move across screens.
                            </p>
                        </div>
                    </aside>
                </div>
            )}
        </main>
    );
}