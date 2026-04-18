// UI constants — no business data.
// Business data is served by the API (src/api/).

export const dashboardDocs = [
  { name: 'Contract', icon: 'description', status: 'Validated' },
  { name: 'Statement', icon: 'note_stack', status: 'Validated' },
  { name: 'Dossier', icon: 'folder_shared', status: 'Missing', tone: 'danger' },
  { name: 'Debt Evolution', icon: 'analytics', status: 'Inconsistent', tone: 'warning' },
];

export const riskIndicators = [
  { label: 'Document Authenticity Score', value: 94, color: 'primary' },
  { label: 'Winning Probability', value: 35, color: 'danger' },
  { label: 'Estimated Savings', value: 12, color: 'tertiary' },
];

// Skeleton cards shown while metrics are loading for the first time
export const statsCards = [
  { label: 'Total Decisions', value: '—', note: '— processes', icon: 'task_alt' },
  { label: 'Settlement Adherence', value: '—', note: 'On Target', icon: 'verified_user' },
  { label: 'Total Savings', value: '—', note: 'vs litigation cost', icon: 'payments' },
  { label: 'High-Risk Cases', value: '—', note: 'Confidence < 60%', icon: 'warning' },
];
