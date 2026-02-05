-- 1. Habilitar a extensão pgvector (se já não estiver ativa)
create extension if not exists vector;

-- 2. Tabela de Agendamentos (O "Córtex Prefrontal")
-- Armazena compromissos futuros, lembretes e tarefas.
create table if not exists scheduled_tasks (
  id uuid primary key default gen_random_uuid(),
  created_at timestamp with time zone default now(),
  scheduled_at timestamp with time zone not null, -- Quando deve ser executado
  description text not null, -- O que deve ser feito (ex: "Lembrar de tomar água")
  status text not null default 'pending', -- 'pending', 'completed', 'failed', 'cancelled'
  user_id uuid, -- Opcional, se quiser multi-usuário no futuro
  metadata jsonb default '{}'::jsonb -- Dados extras flexíveis
);

-- Índices para busca rápida no loop (o Caio vai verificar isso a cada minuto)
create index if not exists idx_scheduled_tasks_status on scheduled_tasks(status);
create index if not exists idx_scheduled_tasks_scheduled_at on scheduled_tasks(scheduled_at);

-- 3. Tabela de Memória Semântica (O "Hipocampo")
-- Armazena fatos, sentimentos e histórico para recuperação contextual.
create table if not exists memories (
  id uuid primary key default gen_random_uuid(),
  created_at timestamp with time zone default now(),
  content text not null, -- O texto da memória (ex: "O usuário disse que está cansado hoje")
  embedding vector(1536), -- Vetor de 1536 dimensões (Padrão OpenAI experimente text-embedding-3-small)
  source text default 'chat', -- De onde veio? 'chat', 'email', 'system'
  importance int default 1 -- 1 a 10: quão importante é essa memória?
);

-- Índice HNSW para busca vetorial ultrarrápida (IVFFlat também serve, mas HNSW é melhor pro 'Caio')
create index if not exists idx_memories_embedding on memories using hnsw (embedding vector_cosine_ops);
