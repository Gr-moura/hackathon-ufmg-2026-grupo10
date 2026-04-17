# Política de Acordos — Banco UFMG

> Versão `1.0` · Para linguagem técnica dos parâmetros, ver `src/back/policy.yaml`.

## Contexto

Este documento descreve, em linguagem acessível ao time jurídico, a política de acordos adotada pelo Banco UFMG para processos de **não reconhecimento de contratação de empréstimo consignado**.

## Regra de Decisão

A recomendação de **ACORDO** ou **DEFESA** é calculada com base em três eixos:

1. **Completude documental** — presença de contrato assinado, comprovante de crédito (BACEN), dossiê de autenticidade e extrato bancário.
2. **Sinais de fraude vs. legitimidade** — extraídos automaticamente dos documentos do processo.
3. **Histórico de sentenças similares** — comparação com os ~60.000 casos históricos do banco para estimar a probabilidade de êxito.

## Limites do Valor de Acordo

| Parâmetro | Valor |
|-----------|-------|
| Piso (% do valor da causa) | 30% |
| Teto (% do valor da causa) | 70% |
| Piso absoluto | R$ 1.500,00 |
| Teto absoluto | R$ 50.000,00 |

## Nível de Confiança da IA

| Cor | Confidence | Ação |
|-----|-----------|------|
| Verde | ≥ 0,85 | Advogado pode aprovar com 1 clique |
| Amarelo | 0,60–0,85 | Requer justificativa se advogado divergir |
| Vermelho | < 0,60 | Bloqueia auto-aprovação; exige revisão de supervisor |

## Flags que Forçam Defesa

- Assinatura evidentemente falsificada no dossiê
- Ausência total de comprovante de crédito (BACEN)

## Calibração e Revisão

Os parâmetros acima estão em `src/back/policy.yaml` e são lidos pela API a cada requisição — **sem necessidade de deploy** para ajustes de calibração.
