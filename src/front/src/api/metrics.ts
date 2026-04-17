import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type { MetricsResponse, RecommendationFeedItem } from './types';

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      const res = await apiClient.get<MetricsResponse>('/dashboard/metrics');
      return res.data;
    },
    refetchInterval: 30_000,
  });
}

export function useRecommendations() {
  return useQuery({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const res = await apiClient.get<RecommendationFeedItem[]>('/dashboard/recommendations');
      return res.data;
    },
    refetchInterval: 15_000,
  });
}
