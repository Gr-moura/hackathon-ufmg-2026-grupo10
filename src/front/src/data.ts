export type ViewKey = 'login' | 'upload' | 'dashboard' | 'monitoring';

export const views: Array<{ key: ViewKey; label: string; icon: string; path: string }> = [
  { key: 'login', label: 'Login', icon: 'lock', path: '/login' },
  { key: 'upload', label: 'File Hub', icon: 'upload_file', path: '/upload' },
  { key: 'dashboard', label: 'Decision Lab', icon: 'gavel', path: '/dashboard' },
  { key: 'monitoring', label: 'Monitoring', icon: 'analytics', path: '/monitoring' },
];

export const navigationItems = [
  { label: 'Dashboard', icon: 'home', path: '/dashboard' },
  { label: 'Process Autos', icon: 'description', path: '/upload' },
  { label: 'Bank Evidence', icon: 'account_balance', path: '/upload' },
  { label: 'Decision Lab', icon: 'gavel', path: '/dashboard' },
  { label: 'Adherence', icon: 'analytics', path: '/monitoring' },
];

export const dashboardDocs = [
  { name: 'Contract', icon: 'description', status: 'Validated' },
  { name: 'Statement', icon: 'note_stack', status: 'Validated' },
  { name: 'Dossier', icon: 'folder_shared', status: 'Missing', tone: 'danger' },
  { name: 'Debt Evolution', icon: 'analytics', status: 'Inconsistent', tone: 'warning' },
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

export const riskIndicators = [
  { label: 'Document Authenticity Score', value: 94, color: 'primary' },
  { label: 'Winning Probability', value: 35, color: 'danger' },
  { label: 'Estimated Savings', value: 12, color: 'tertiary' },
];

export const recommendations = [
  {
    title: 'Settlement Proposal',
    caseId: 'UF-2094 - Consumer Complaint',
    time: '2m ago',
    description: 'Recommended settlement of R$ 12,000 based on previous 82 similar rulings in São Paulo.',
    match: '92% Match',
    tone: 'success',
  },
  {
    title: 'Defense Strategy',
    caseId: 'UF-1822 - Labor Dispute',
    time: '14m ago',
    description: 'AI detected procedural error in filing. Recommendation: Motion to Dismiss.',
    match: 'Policy Exception',
    tone: 'neutral',
  },
  {
    title: 'Urgent Review',
    caseId: 'UF-2101 - Tax Liability',
    time: '1h ago',
    description: 'High-risk flag: Settlement threshold exceeded. Requires Executive intervention.',
    match: 'High Risk',
    tone: 'danger',
  },
  {
    title: 'Settlement Proposal',
    caseId: 'UF-2041 - Credit Card Fraud',
    time: '2h ago',
    description: 'Recommended settlement of R$ 5,500. Alignment with Digital Fraud policy v4.1.',
    match: '100% Match',
    tone: 'success',
  },
];

export const performanceRows = [
  { initials: 'MS', name: 'Mariana Santos', role: 'Senior Associate', cases: 124, adherence: 98, recommended: 'R$ 420k', actual: 'R$ 418k', tone: 'success' },
  { initials: 'RB', name: 'Ricardo Barbosa', role: 'Junior Partner', cases: 98, adherence: 72, recommended: 'R$ 310k', actual: 'R$ 390k', tone: 'warning' },
  { initials: 'LV', name: 'Lucia Viana', role: 'Outsourced', cases: 242, adherence: 91, recommended: 'R$ 1.2M', actual: 'R$ 1.1M', tone: 'success' },
];

export const statsCards = [
  { label: 'Total Decisions', value: '1,429', note: '+12% vs LY', icon: 'task_alt' },
  { label: 'Settlement Adherence', value: '94.2%', note: 'On Target', icon: 'verified_user' },
  { label: 'Total Savings', value: 'R$ 2.4M', note: 'R$ 240k Saved', icon: 'payments' },
  { label: 'High-Risk Cases', value: '42', note: 'Live Attention', icon: 'warning' },
];