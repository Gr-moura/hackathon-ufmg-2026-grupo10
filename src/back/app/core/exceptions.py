class DocumentParsingError(Exception):
    """Raised when a document cannot be parsed by the ingestion pipeline."""

    def __init__(self, doc_name: str, reason: str, recoverable: bool) -> None:
        self.doc_name = doc_name
        self.reason = reason
        self.recoverable = recoverable
        super().__init__(f"Falha ao processar '{doc_name}': {reason} (recuperável={recoverable})")


class ProcessNotFoundError(Exception):
    def __init__(self, processo_id: str) -> None:
        super().__init__(f"Processo {processo_id} não encontrado")


class AnalysisNotFoundError(Exception):
    def __init__(self, processo_id: str) -> None:
        super().__init__(f"Análise para processo {processo_id} não encontrada")
