import uuid
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.db.models.processo import Processo
from app.db.models.analise_ia import AnaliseIA
from app.db.models.proposta_acordo import PropostaAcordo
from app.db.models.decisao_advogado import DecisaoAdvogado
from app.core.logging import configure_logging

configure_logging()

def seed_demo_data():
    db = SessionLocal()
    advogado_id = "00000000-0000-0000-0000-000000000001" # Mock Lawyer
    
    print("Iniciando seed de dados de demonstração...")

    for i in range(15):
        # 1. Criar Processo
        days_ago = random.randint(0, 7)
        created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
        processo = Processo(
            id=uuid.uuid4(),
            numero_processo=f"{2024}{random.randint(100000, 999999)}",
            advogado_id=advogado_id,
            valor_causa=random.uniform(5000, 50000),
            status="concluido" if i < 12 else "analisado",
            created_at=created_at
        )
        db.add(processo)
        db.flush()

        # 2. Criar Analise IA
        decisao = random.choice(["ACORDO", "DEFESA"])
        confidence = random.uniform(0.65, 0.98)
        
        analise = AnaliseIA(
            id=uuid.uuid4(),
            processo_id=processo.id,
            decisao=decisao,
            confidence=confidence,
            rationale="Análise baseada em precedentes similares na mesma UF e vara cível.",
            fatores_pro_acordo=["Baixo risco de sucumbência", "Valor dentro da média histórica"],
            fatores_pro_defesa=["Documentação do banco robusta"],
            requires_supervisor=confidence < 0.75,
            created_at=created_at
        )
        db.add(analise)
        db.flush()

        # 3. Criar Proposta se for Acordo
        if decisao == "ACORDO":
            valor_sug = processo.valor_causa * 0.4
            proposta = PropostaAcordo(
                id=uuid.uuid4(),
                analise_id=analise.id,
                valor_sugerido=valor_sug,
                valor_base_estatistico=valor_sug * 0.95,
                modulador_llm=1.05,
                intervalo_min=valor_sug * 0.8,
                intervalo_max=valor_sug * 1.2,
                custo_estimado_litigar=processo.valor_causa * 0.6,
                n_casos_similares=random.randint(5, 45)
            )
            db.add(proposta)

        # 4. Criar Decisão do Advogado (HITL) para os concluídos
        if i < 12:
            # 80% de aderência para o mock ficar bonito
            aderiu = random.random() < 0.8
            acao = "ACEITAR" if aderiu else random.choice(["AJUSTAR", "RECUSAR"])
            
            decisao_adv = DecisaoAdvogado(
                id=uuid.uuid4(),
                analise_id=analise.id,
                acao=acao,
                valor_advogado=proposta.valor_sugerido if (decisao=="ACORDO" and acao=="ACEITAR") else None,
                justificativa="Dentro da política do banco." if acao=="ACEITAR" else "Valor muito elevado para a comarca.",
                advogado_id=advogado_id,
                created_at=created_at + timedelta(hours=2)
            )
            db.add(decisao_adv)

    db.commit()
    print("Seed concluído com sucesso!")

if __name__ == "__main__":
    seed_demo_data()
