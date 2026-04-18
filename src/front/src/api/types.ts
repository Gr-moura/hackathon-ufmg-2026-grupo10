export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
  name: string;
}

export interface DocumentoResponse {
  id: string;
  doc_type: string;
  original_filename: string;
  page_count: number;
  parse_errors: Array<{ stage: string; reason: string }> | null;
}

export interface MetadataExtraida {
  uf: string | null;
  sub_assunto: string | null;
  valor_da_causa: number | null;
}

export interface ProcessoResponse {
  id: string;
  numero_processo: string;
  advogado_id: string;
  valor_causa: number | null;
  status: string;
  created_at: string;
  documentos: DocumentoResponse[];
  metadata_extraida: MetadataExtraida | null;
}

export interface ProcessoListItem {
  id: string;
  numero_processo: string;
  status: string;
  created_at: string;
  n_documentos: number;
}

export type Decisao = 'ACORDO' | 'DEFESA';
export type AcaoAdvogado = 'ACEITAR' | 'AJUSTAR' | 'RECUSAR';

export interface TrechoChave {
  doc: string;
  page: number;
  quote: string;
}

export interface PropostaAcordoResponse {
  valor_sugerido: number;
  intervalo_min: number;
  intervalo_max: number;
  custo_estimado_litigar: number;
  economia_esperada: number;
  n_casos_similares: number;
}

export interface AnaliseIAResponse {
  id: string;
  processo_id: string;
  decisao: Decisao;
  confidence: number;
  rationale: string;
  fatores_pro_acordo: string[];
  fatores_pro_defesa: string[];
  requires_supervisor: boolean;
  proposta: PropostaAcordoResponse | null;
  trechos_chave: TrechoChave[];
}

export interface DecisaoAdvogadoRequest {
  acao: AcaoAdvogado;
  valor_advogado?: number | null;
  justificativa?: string | null;
}

export interface MetricsResponse {
  total_processos: number;
  total_decisoes: number;
  aderencia_global: number | null;
  economia_total: number | null;
  casos_alto_risco: number;
  aderencia_por_advogado: Array<{
    advogado_id: string;
    total: number;
    aceitos: number;
    aderencia: number;
  }>;
  drift_confianca: Array<{ dia: string; avg_confidence: number }>;
}

export interface RecommendationFeedItem {
  processo_id: string;
  numero_processo: string;
  decisao: string;
  confidence: number;
  valor_sugerido: number | null;
  created_at: string;
}
