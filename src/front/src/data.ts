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



export const uploadCategories = [
  {
    title: 'Contract',
    icon: 'contract',
    description: 'Original signed agreements and terms of service documentation.',
    tag: 'Required',
  },
  {
    title: 'Bank Statement',
    icon: 'receipt_long',
    description: 'Transactional history including deposits and relevant debits.',
    tag: 'Automated',
  },
  {
    title: 'Credit Voucher',
    icon: 'payments',
    description: 'Proof of credit release or settlement payment confirmations.',
    tag: 'Verification',
  },
];

export const recentFiles = [
  { name: 'Autos_2024_Case_89.pdf', time: 'Processed 12m ago', size: '4.2 MB', status: 'Validated' },
  { name: 'Bank_Subsidy_Voucher_X.pdf', time: 'Processed 45m ago', size: '1.1 MB', status: 'Missing', tone: 'danger' },
];