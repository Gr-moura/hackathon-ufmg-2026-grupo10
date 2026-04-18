# Importar todos os models garante que o Alembic os detecte no autogenerate
from app.db.models.analise_ia import AnaliseIA
from app.db.models.decisao_advogado import DecisaoAdvogado
from app.db.models.documento import Documento
from app.db.models.processo import Processo
from app.db.models.proposta_acordo import PropostaAcordo
from app.db.models.sentenca_historica import SentencaHistorica

__all__ = [
    "AnaliseIA",
    "DecisaoAdvogado",
    "Documento",
    "Processo",
    "PropostaAcordo",
    "SentencaHistorica",
]
