// UI constants — no business data.
// Business data is served by the API (src/api/).

export const dashboardDocs = [
  { name: 'Contrato', icon: 'description', status: 'Validado' },
  { name: 'Extrato', icon: 'note_stack', status: 'Validado' },
  { name: 'Dossiê', icon: 'folder_shared', status: 'Ausente', tone: 'danger' },
  { name: 'Evolução da dívida', icon: 'analytics', status: 'Inconsistente', tone: 'warning' },
];

export const riskIndicators = [
  { label: 'Autenticidade documental', value: 94, color: 'primary' },
  { label: 'Probabilidade de êxito', value: 35, color: 'danger' },
  { label: 'Economia estimada', value: 12, color: 'tertiary' },
];

// Cards esqueleto mostrados enquanto as métricas carregam pela primeira vez
export const statsCards = [
  { label: 'Total de Decisões', value: '—', note: '— processos', icon: 'task_alt' },
  { label: 'Aderência a Acordos', value: '—', note: 'Dentro da meta', icon: 'verified_user' },
  { label: 'Economia Total', value: '—', note: 'vs. custo de litígio', icon: 'payments' },
  { label: 'Casos de Alto Risco', value: '—', note: 'Confiança < 60%', icon: 'warning' },
];



export const uploadCategories = [
  {
    title: 'Contrato',
    icon: 'contract',
    description: 'Contratos assinados originais e termos de serviço.',
    tag: 'Obrigatório',
  },
  {
    title: 'Extrato bancário',
    icon: 'receipt_long',
    description: 'Histórico de transações com depósitos e débitos relevantes.',
    tag: 'Automatizado',
  },
  {
    title: 'Comprovante de crédito',
    icon: 'payments',
    description: 'Comprovante de liberação de crédito ou confirmação de quitação.',
    tag: 'Verificação',
  },
];

export const recentFiles = [
  { name: 'Autos_2024_Caso_89.pdf', time: 'Processado há 12min', size: '4.2 MB', status: 'Validado' },
  { name: 'Comprovante_Banco_X.pdf', time: 'Processado há 45min', size: '1.1 MB', status: 'Ausente', tone: 'danger' },
];
