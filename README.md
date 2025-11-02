*Classificador de Extratos Financeiros*

link acesso ao Programa: https://finclass-fastapi-cuwotbs8bsvnhupywhzknq.streamlit.app/
link acesso da API https://finclass-fastapi.onrender.com
link acesso ao Programa

O projeto tem como objetivo automatizar a classificação de transações financeiras presentes em extratos bancários, transformando dados brutos em informações organizadas por categoria de consumo.
A proposta é facilitar a análise de gastos e receitas, oferecendo uma visão clara do fluxo financeiro e permitindo ajustes manuais quando necessário.

Durante o desenvolvimento, o foco principal foi garantir precisão, consistência e praticidade. Um dos primeiros desafios enfrentados foi a variação de formatos nos arquivos de extrato,
já que diferentes instituições usam nomes de colunas e estruturas distintas. Para resolver esse problema, foi utilizada validação com Pydantic, garantindo que o arquivo possuísse as colunas 
essenciais e convertendo automaticamente nomes diferentes (“Descrição”, “Histórico”, “Valor (R$)”) para um padrão único reconhecido pelo sistema.

Outro ponto central foi a criação do mecanismo de classificação automática. Para isso, foi desenvolvido um dicionário de categorias que agrupa palavras-chave e marcas conhecidas em subcategorias específicas 
por exemplo, supermercados, transporte, assinaturas, bancos e aplicativos. A análise foi implementada com Pandas, utilizando expressões regulares para comparar as descrições das transações com as palavras
definidas no dicionário.
Para aumentar a precisão, foi adotada uma regra de prioridade por tamanho de palavra, de forma que termos mais longos prevalecem sobre expressões curtas e genéricas, reduzindo falsos positivos.

As transações também foram divididas entre entradas e saídas, com base no sinal do valor: valores positivos são considerados entradas e negativos, saídas. Essa separação evita que categorias 
incompatíveis sejam atribuídas a tipos de operação incorretos, garantindo maior coerência na análise.

Para os casos em que a classificação automática não encontra correspondência, o sistema cria uma categoria padrão chamada “Não Classificado”. Isso assegura que todas as transações sejam exibidas
e analisadas, mesmo que algumas ainda não possuam uma categoria definida.

A reclassificação manual foi adicionada para dar mais flexibilidade ao usuário. Através da interface em Streamlit, é possível visualizar as transações, filtrar por categoria e alterar manualmente 
qualquer linha incorretamente classificada. A atualização é feita em tempo real por meio de uma API FastAPI, que persiste as mudanças e atualiza o conjunto de dados armazenado.

A interface também apresenta gráficos interativos que mostram o consumo por categoria e os totais de entradas e saídas, permitindo uma visualização rápida e intuitiva do comportamento financeiro.

O projeto está dividido em três partes principais:

Backend FastAPI: responsável por receber os arquivos, validar, processar e classificar as transações.

Classificador Pandas: núcleo que executa a lógica de categorização, agrupamento e cálculo de totais.

Frontend Streamlit: interface que exibe os gráficos, tabelas de transações e permite a reclassificação manual.

Cada etapa do desenvolvimento foi pensada para resolver problemas práticos de organização e precisão: a validação com Pydantic garante integridade dos dados; o classificador com Pandas
identifica categorias com base em similaridade textual; e a interface com Streamlit torna a análise acessível e ajustável pelo usuário.

O próximo passo do projeto é o uso de machine learning para aperfeiçoar a classificação. A ideia é que as reclassificações manuais sirvam como base de aprendizado, permitindo que o sistema 
aprenda novos padrões e reduza, gradualmente, o número de transações não classificadas.
