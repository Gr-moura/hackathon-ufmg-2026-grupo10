/**
 * MSW v2 handlers — interceptam chamadas HTTP dos hooks TanStack Query.
 * Base URL: http://localhost:8000 (fallback do VITE_API_BASE_URL em testes jsdom)
 */
import { http, HttpResponse } from 'msw';
import type {
  AnaliseIAResponse,
  MetricsResponse,
  ProcessoListItem,
  ProcessoResponse,
  RecommendationFeedItem,
  TokenResponse,
} from '../../api/types';

const BASE = 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Fixtures reutilizáveis
// ---------------------------------------------------------------------------

export const MOCK_TOKEN: TokenResponse = {
  access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock.signature',
  token_type: 'bearer',
  role: 'advogado',
  name: 'Dr. João Silva',
};

export const MOCK_PROCESSO: ProcessoResponse = {
  id: '00000000-0000-0000-0000-000000000010',
  numero_processo: '0001234-56.2024.8.13.0001',
  advogado_id: '00000000-0000-0000-0000-000000000001',
  valor_causa: 15000,
  status: 'pendente',
  created_at: '2026-04-17T10:00:00Z',
  metadata_extraida: { uf: 'MG', sub_assunto: 'generico', valor_da_causa: 15000 },
  documentos: [
    {
      id: '00000000-0000-0000-0000-000000000020',
      doc_type: 'PETICAO_INICIAL',
      original_filename: 'peticao_inicial.pdf',
      page_count: 3,
      parse_errors: null,
    },
  ],
  metadata_extraida: { uf: 'MG', sub_assunto: 'generico', valor_da_causa: 15000 },
};

export const MOCK_PROCESSO_LIST: ProcessoListItem[] = [
  {
    id: MOCK_PROCESSO.id,
    numero_processo: MOCK_PROCESSO.numero_processo,
    status: 'pendente',
    created_at: MOCK_PROCESSO.created_at,
    n_documentos: 1,
  },
];

// [D1] valor_sugerido como string — comportamento real do Pydantic v2 com Decimal
export const MOCK_ANALISE: AnaliseIAResponse = {
  id: '00000000-0000-0000-0000-000000000030',
  processo_id: MOCK_PROCESSO.id,
  decisao: 'ACORDO',
  confidence: 0.88,
  rationale: 'Alta similaridade com 30 casos históricos de empréstimos não reconhecidos.',
  fatores_pro_acordo: ['pagamento_no_extrato', 'dossie_presente'],
  fatores_pro_defesa: ['valor_causa_elevado'],
  requires_supervisor: false,
  proposta: {
    // O backend retorna strings aqui (Decimal → str via Pydantic v2).
    // O TypeScript diz `number` — discrepância [D1]. Number() no front contorna isso.
    valor_sugerido: 5000 as unknown as number,
    intervalo_min: 4000 as unknown as number,
    intervalo_max: 6500 as unknown as number,
    custo_estimado_litigar: 12000 as unknown as number,
    economia_esperada: 7000 as unknown as number,
    n_casos_similares: 30,
  },
  trechos_chave: [
    { doc: 'peticao_inicial', page: 1, quote: 'o autor alega não reconhecer o contrato' },
  ],
};

export const MOCK_METRICS: MetricsResponse = {
  total_processos: 5,
  total_decisoes: 3,
  aderencia_global: 0.6667,
  economia_total: 21000,
  casos_alto_risco: 1,
  aderencia_por_advogado: [
    { advogado_id: '00000000-0000-0000-0000-000000000001', total: 3, aceitos: 2, aderencia: 0.6667 },
  ],
  drift_confianca: [{ dia: '2026-04-17', avg_confidence: 0.82 }],
};

export const MOCK_RECOMMENDATIONS: RecommendationFeedItem[] = [
  {
    processo_id: MOCK_PROCESSO.id,
    numero_processo: MOCK_PROCESSO.numero_processo,
    decisao: 'ACORDO',
    confidence: 0.88,
    valor_sugerido: 5000,
    created_at: '2026-04-17T10:00:00.000000',
  },
];

// ---------------------------------------------------------------------------
// Handlers padrão (happy path)
// ---------------------------------------------------------------------------

export const handlers = [
  http.post(`${BASE}/auth/login`, () => HttpResponse.json(MOCK_TOKEN)),

  http.get(`${BASE}/processes`, () => HttpResponse.json(MOCK_PROCESSO_LIST)),

  http.post(`${BASE}/processes`, () => HttpResponse.json(MOCK_PROCESSO, { status: 201 })),

  http.get(`${BASE}/processes/:processoId`, ({ params }) => {
    if (params['processoId'] === MOCK_PROCESSO.id) {
      return HttpResponse.json(MOCK_PROCESSO);
    }
    return HttpResponse.json({ detail: 'Processo não encontrado' }, { status: 404 });
  }),

  http.post(`${BASE}/processes/:processoId/analyze`, ({ params }) => {
    if (params['processoId'] === MOCK_PROCESSO.id) {
      return HttpResponse.json(MOCK_ANALISE);
    }
    return HttpResponse.json({ detail: 'Processo não encontrado' }, { status: 404 });
  }),

  http.get(`${BASE}/processes/:processoId/analysis`, ({ params }) => {
    if (params['processoId'] === MOCK_PROCESSO.id) {
      return HttpResponse.json(MOCK_ANALISE);
    }
    return HttpResponse.json({ detail: 'Análise não encontrada' }, { status: 404 });
  }),

  http.post(`${BASE}/processes/analysis/:analiseId/decision`, () =>
    new HttpResponse(null, { status: 204 }),
  ),

  http.get(`${BASE}/dashboard/metrics`, () => HttpResponse.json(MOCK_METRICS)),

  http.get(`${BASE}/dashboard/recommendations`, () =>
    HttpResponse.json(MOCK_RECOMMENDATIONS),
  ),
];
