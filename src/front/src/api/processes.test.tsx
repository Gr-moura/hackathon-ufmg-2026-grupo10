import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useProcessos, useProcesso, useAnalyzeProcesso, useRegisterDecision } from './processes';
import { createWrapper } from '../tests/utils';
import { MOCK_PROCESSO, MOCK_PROCESSO_LIST } from '../tests/mocks/handlers';

describe('Processes Hooks', () => {
  it('useProcessos should return a list of processes', async () => {
    const { result } = renderHook(() => useProcessos(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(MOCK_PROCESSO_LIST);
  });

  it('useProcesso should return a single process', async () => {
    const { result } = renderHook(() => useProcesso(MOCK_PROCESSO.id), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(MOCK_PROCESSO);
  });

  it('useAnalyzeProcesso returns the analysis payload on success', async () => {
    const { result } = renderHook(() => useAnalyzeProcesso(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(MOCK_PROCESSO.id);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.processo_id).toBe(MOCK_PROCESSO.id);
    expect(result.current.data?.decisao).toBe('ACORDO');
  });

  it('useRegisterDecision should succeed with 204', async () => {
    const { result } = renderHook(() => useRegisterDecision(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      analiseId: 'analise-id',
      acao: 'ACEITAR',
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
