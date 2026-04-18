import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../../modules/ui/Icon';
import { ExecutiveMonitoringDashboard } from '../../modules/ui/ExecutiveMonitoringDashboard/ExecutiveMonitoringDashboard';
import type { UserRole } from '../../modules/ui/LoginRoleSelector/LoginRoleSelector';
import './Home.css';

const homeCapabilities = [
    {
        icon: 'folder_open',
        title: 'Abertura estruturada de casos',
        description: 'Crie áreas de trabalho com metadados padronizados para que cada caso comece com a mesma base operacional.',
    },
    {
        icon: 'account_tree',
        title: 'Orquestração do fluxo de decisão',
        description: 'Coordene a passagem de etapa entre as fases jurídicas com checkpoints claros e responsabilidades transparentes.',
    },
    {
        icon: 'shield_lock',
        title: 'Governança e rastreabilidade',
        description: 'Mantenha decisões, anotações e trilhas de evidência audítaveis durante todo o ciclo de vida do processo.',
    },
];

const workflowSteps = [
    'Defina o objetivo e a prioridade do caso.',
    'Abra o módulo desejado pela barra lateral para continuar o fluxo.',
    'Acompanhe os resultados e mantenha a consistência do processo pela plataforma.',
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
                    label: 'Monitoramento',
                    path: '/monitoring',
                    icon: 'analytics',
                    description: 'Abra a central de monitoramento para acompanhar os indicadores operacionais.',
                }
            : {
                    label: 'Nova análise',
                    path: '/upload',
                    icon: 'playlist_add',
                    description: 'Inicie um novo fluxo de análise e conduza o caso pela plataforma.',
                };

    return (
        <main className="screen home-screen">
            <section className="panel panel-inner hero-banner home-screen__hero">
                <div className="title-kicker">Bem-vindo</div>
                <h1 className="headline home-screen__headline">Área de Operações Jurídicas</h1>
                <p className="lede home-screen__lede">
                    Um ambiente único para organizar as rotinas jurídicas, manter os times alinhados e conduzir cada caso por uma jornada operacional clara.
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
                            <h3 className="section-title">Capacidades da plataforma</h3>
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
                            <h3 className="section-title">Fluxo diário</h3>
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
                            <h4 className="section-title-strong home-screen__support-title">Dica de navegação</h4>
                            <p className="muted home-screen__support-copy">
                                Use a barra lateral a qualquer momento para trocar de módulo. O EanterOS mantém o contexto operacional consistente entre as telas.
                            </p>
                        </div>
                    </aside>
                </div>
            )}
        </main>
    );
}