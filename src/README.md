# Coloque aqui o código-fonte da sua solução.

Não há restrição de linguagem ou tecnologia — use o que sua equipe domina melhor.

## Sugestões de organização

```
src/
├── policy/        # lógica da política de acordos (regras de decisão, sugestão de valor)
├── interface/     # interface de acesso do advogado à recomendação
    |- Frontend/     # interface gráfica (web, desktop, etc.)
    |- Backend/      # API, lógica de comunicação, etc.
    |- Database/     # modelos de dados, acesso a banco, etc.
└── utils/         # utilitários compartilhados
```

> Sinta-se livre para reorganizar conforme a arquitetura da sua solução.

## Frontend

Uma implementação React/Vite do front está disponível em [`src/front`](./front). Ela reúne as telas de login, upload, decisão e monitoramento em uma única aplicação navegável.
