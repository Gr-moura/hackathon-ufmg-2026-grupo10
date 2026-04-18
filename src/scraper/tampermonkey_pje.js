// ==UserScript==
// @name         PJe — Auto Download PDFs
// @namespace    hackathon-grupo10
// @version      1.0
// @description  Na página de consulta pública do PJe, clica no processo e baixa todos os PDFs automaticamente
// @match        https://pje.tjam.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjal.jus.br/pje/ConsultaPublica/*
// @match        https://pje2.tjal.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjce.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjma.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjpb.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjpe.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjpi.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjrn.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjse.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjto.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjac.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjap.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjro.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjrr.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjpa.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjgo.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjmt.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjms.jus.br/pje/ConsultaPublica/*
// @match        https://pje.tjdft.jus.br/pje/ConsultaPublica/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    const DELAY = 1500; // ms entre ações

    function esperar(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function log(msg) {
        console.log('[PJe-AutoDownload]', msg);
    }

    // Baixa um PDF via link invisível
    function baixarUrl(url, nome) {
        const a = document.createElement('a');
        a.href = url;
        a.download = nome || 'documento.pdf';
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // Tenta encontrar e clicar no primeiro resultado de processo
    async function clicarProcesso() {
        await esperar(DELAY);
        const linksProcesso = [
            ...document.querySelectorAll('a[href*="detalhe"], a[href*="Detalhe"], a[href*="processo"]')
        ].filter(a => a.textContent.trim().length > 5);

        if (linksProcesso.length === 0) {
            log('Nenhum processo encontrado na listagem');
            return false;
        }
        log(`Clicando no processo: ${linksProcesso[0].textContent.trim()}`);
        linksProcesso[0].click();
        return true;
    }

    // Baixa todos os PDFs visíveis na página de detalhe
    async function baixarDocumentos() {
        await esperar(DELAY * 2);

        // Seletores comuns de documentos no PJe
        const seletores = [
            'a[href*=".pdf"]',
            'a[href*="documento"]',
            'a[href*="arquivo"]',
            'a[href*="download"]',
            'span[onclick*="pdf"]',
            'a[title*="PDF"]',
            'a[title*="Visualizar"]',
        ];

        const links = new Set();
        seletores.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                const href = el.href || el.getAttribute('onclick');
                if (href) links.add({ href, texto: el.textContent.trim() || el.title || 'documento' });
            });
        });

        if (links.size === 0) {
            log('Nenhum documento encontrado — pode ser processo sigiloso ou sem documentos públicos');
            return;
        }

        log(`Baixando ${links.size} documento(s)…`);
        let i = 1;
        for (const { href, texto } of links) {
            await esperar(800);
            const nome = `doc_${String(i).padStart(2, '0')}_${texto.slice(0, 30).replace(/\W+/g, '_')}.pdf`;
            baixarUrl(href, nome);
            log(`  Baixado: ${nome}`);
            i++;
        }

        // Fecha a aba após os downloads (opcional — comente se não quiser)
        await esperar(2000);
        window.close();
    }

    // Fluxo principal
    async function main() {
        const url = window.location.href;
        const temNumero = url.includes('numeroProcesso=');

        if (!temNumero) {
            log('URL sem número de processo — aguardando navegação');
            return;
        }

        // Estamos na listagem — clica no processo
        const estaNoDetalhe = url.includes('detalhe') || url.includes('Detalhe');
        if (!estaNoDetalhe) {
            const clicou = await clicarProcesso();
            if (!clicou) return;
            // Aguarda navegação para a página de detalhe
            await esperar(3000);
            // O script será executado novamente na nova página
        } else {
            // Já estamos na página de detalhe — baixa documentos
            await baixarDocumentos();
        }
    }

    main();
})();
