import { useNavigate } from 'react-router-dom';
import { useProcessos, useAnalyzeProcesso } from '../../api/processes';
import { Icon } from '../../modules/ui/Icon';
import './ProcessListScreen.css';

const STATUS_LABEL: Record<string, string> = {
  pendente: 'Pendente',
  processando: 'Processando',
  analisado: 'Analisado',
  concluido: 'Concluído',
};

const STATUS_TONE: Record<string, string> = {
  pendente: '',
  processando: 'warning',
  analisado: 'success',
  concluido: 'success',
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function ProcessListScreen() {
  const navigate = useNavigate();
  const { data: processos, isLoading, isError, refetch } = useProcessos();
  const analyze = useAnalyzeProcesso();

  async function handleAnalyze(processoId: string) {
    await analyze.mutateAsync(processoId);
    navigate(`/dashboard/${processoId}`);
  }

  return (
    <main className="screen process-list-screen">
      <section className="panel panel-inner process-list-screen__header">
        <div className="section-heading">
          <div>
            <h1 className="section-title-strong process-list-screen__title">Mesa de Decisão</h1>
            <p className="section-text process-list-screen__subtitle">
              Selecione um caso para ver ou executar a análise de IA.
            </p>
          </div>
          <button
            type="button"
            className="primary-button"
            onClick={() => navigate('/upload')}
          >
            <Icon name="add" /> Novo caso
          </button>
        </div>
      </section>

      <section className="panel panel-inner process-list-screen__list-panel">
        {isLoading && (
          <p className="muted" style={{ textAlign: 'center', padding: 32 }}>Carregando casos…</p>
        )}
        {isError && (
          <div style={{ textAlign: 'center', padding: 32 }}>
            <p className="muted" style={{ marginBottom: 12 }}>Falha ao carregar casos.</p>
            <button className="ghost-button" onClick={() => refetch()}>Tentar novamente</button>
          </div>
        )}
        {processos && processos.length === 0 && (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <div className="doc-icon" style={{ margin: '0 auto 16px' }}><Icon name="folder_open" /></div>
            <p className="section-title-strong" style={{ marginBottom: 8 }}>Nenhum caso ainda</p>
            <p className="muted" style={{ marginBottom: 20 }}>
              Faça upload de documentos para iniciar sua primeira análise.
            </p>
            <button className="primary-button" onClick={() => navigate('/upload')}>
              <Icon name="upload_file" /> Ir para Central de Evidências
            </button>
          </div>
        )}
        {processos && processos.length > 0 && (
          <div className="table-wrap">
            <table className="data-table process-list-screen__table">
              <thead>
                <tr>
                  <th>Processo</th>
                  <th>Documentos</th>
                  <th>Data</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Ação</th>
                </tr>
              </thead>
              <tbody>
                {processos.map((p) => {
                  const isAnalyzed = p.status === 'analisado' || p.status === 'concluido';
                  const isProcessing = analyze.isPending && analyze.variables === p.id;
                  return (
                    <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => isAnalyzed && navigate(`/dashboard/${p.id}`)}>
                      <td>
                        <div className="row-head">
                          <div className="avatar">{p.numero_processo.slice(0, 2).toUpperCase()}</div>
                          <div>
                            <strong style={{ fontSize: '0.85rem' }}>{p.numero_processo}</strong>
                          </div>
                        </div>
                      </td>
                      <td className="muted">{p.n_documentos} doc{p.n_documentos !== 1 ? 's' : ''}</td>
                      <td className="muted" style={{ fontSize: '0.82rem' }}>{formatDate(p.created_at)}</td>
                      <td>
                        <span className={`status-pill ${STATUS_TONE[p.status] ?? ''}`}>
                          {STATUS_LABEL[p.status] ?? p.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {isAnalyzed ? (
                          <button
                            className="ghost-button"
                            onClick={(e) => { e.stopPropagation(); navigate(`/dashboard/${p.id}`); }}
                          >
                            <Icon name="open_in_new" /> Ver análise
                          </button>
                        ) : (
                          <button
                            className="primary-button"
                            disabled={analyze.isPending}
                            onClick={(e) => { e.stopPropagation(); handleAnalyze(p.id); }}
                          >
                            {isProcessing ? 'Analisando…' : <><Icon name="auto_awesome" /> Analisar</>}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
