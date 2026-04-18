import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
  AnaliseIAResponse,
  AcaoAdvogado,
  DecisaoAdvogadoRequest,
  ProcessoListItem,
  ProcessoResponse,
} from './types';

export function useLogin() {
  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const form = new URLSearchParams({ username: email, password });
      const res = await apiClient.post('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      return res.data as { access_token: string; role: string; name: string };
    },
  });
}

export function useUploadProcesso() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      numeroProcesso: string;
      valorCausa?: number;
      files: File[];
    }) => {
      const form = new FormData();
      form.append('numero_processo', data.numeroProcesso);
      if (data.valorCausa != null) form.append('valor_causa', String(data.valorCausa));
      data.files.forEach((f) => form.append('files', f));
      const res = await apiClient.post<ProcessoResponse>('/processes', form);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['processos'] }),
  });
}

export function useProcessos() {
  return useQuery({
    queryKey: ['processos'],
    queryFn: async () => {
      const res = await apiClient.get<ProcessoListItem[]>('/processes');
      return res.data;
    },
  });
}

export function useProcesso(processoId: string | undefined) {
  return useQuery({
    queryKey: ['processo', processoId],
    queryFn: async () => {
      const res = await apiClient.get<ProcessoResponse>(`/processes/${processoId}`);
      return res.data;
    },
    enabled: !!processoId,
  });
}

export function useAnalyzeProcesso() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (processoId: string) => {
      const res = await apiClient.post<AnaliseIAResponse>(`/processes/${processoId}/analyze`);
      return res.data;
    },
    onSuccess: (data) => {
      qc.setQueryData(['analysis', data.processo_id], data);
    },
  });
}

export function useAnalysis(processoId: string | undefined) {
  return useQuery({
    queryKey: ['analysis', processoId],
    queryFn: async () => {
      const res = await apiClient.get<AnaliseIAResponse>(`/processes/${processoId}/analysis`);
      return res.data;
    },
    enabled: !!processoId,
    retry: false,
  });
}

export function useRegisterDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      analiseId,
      ...body
    }: { analiseId: string } & DecisaoAdvogadoRequest) => {
      await apiClient.post(`/processes/analysis/${analiseId}/decision`, {
        acao: body.acao,
        valor_advogado: body.valor_advogado ?? null,
        justificativa: body.justificativa ?? null,
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['analysis'] }),
  });
}

export function useAnalyzeAndPoll(processoId: string | undefined) {
  const analyze = useAnalyzeProcesso();
  const analysis = useAnalysis(processoId);
  return { analyze, analysis };
}
