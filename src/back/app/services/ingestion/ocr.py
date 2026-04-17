"""OCR fallback para PDFs escaneados usando pytesseract."""
from pathlib import Path

from app.core.exceptions import DocumentParsingError
from app.core.logging import get_logger

logger = get_logger(__name__)


def ocr_pdf(path: Path) -> str:
    """Converte páginas do PDF em imagens e aplica OCR.

    Requer pdfplumber (para renderização) + pytesseract + Tesseract instalado.
    """
    try:
        import pytesseract
        import pdfplumber
    except ImportError as e:
        raise DocumentParsingError(path.name, "dependencia_ocr_ausente", recoverable=True) from e

    try:
        pages_text: list[str] = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    img = page.to_image(resolution=200).original
                    text = pytesseract.image_to_string(img, lang="por")
                    pages_text.append(text)
                except Exception as page_err:
                    logger.warning("OCR falhou na página %d de '%s': %s", i + 1, path.name, page_err)
                    pages_text.append("")

        return "\n".join(pages_text)

    except Exception as e:
        raise DocumentParsingError(path.name, "ocr_falhou", recoverable=True) from e
