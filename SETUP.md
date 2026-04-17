# Setup e Execução

> Preencha este arquivo com as instruções específicas da sua solução.

---

## Pré-requisitos

Liste aqui as dependências necessárias para rodar a solução:

- [ ] Node.js 18+ para o front end React
- [ ] npm ou outro gerenciador compatível

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis necessárias:

```env
# Exemplo — adapte conforme sua solução
OPENAI_API_KEY=sua_chave_aqui
```

> **Nunca commite o arquivo `.env` com credenciais reais.**  
> Um arquivo `.env.example` com as variáveis (sem valores) já está incluído neste repo.

## Instalação

```bash
cd src/front
npm install
```

## Execução

```bash
cd src/front
npm run dev
```

## Dados

Coloque os arquivos de dados fornecidos na pasta `data/`. Consulte [`data/README.md`](./data/README.md) para instruções detalhadas.

## Estrutura do Projeto

```
├── src/          # código-fonte
│   └── front/    # front end React da solução
├── data/         # dados (não versionados — ver .gitignore)
├── docs/         # apresentação e documentação
├── .env.example  # variáveis de ambiente necessárias
├── SETUP.md      # este arquivo
└── README.md     # descrição do desafio
```
