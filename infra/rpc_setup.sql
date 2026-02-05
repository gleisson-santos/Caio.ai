-- ⚠️ Executar no Supabase SQL Editor
-- Correção: Adicionar valores default para os parametros, pois o LangChain nem sempre envia todos.

create or replace function match_memories (
  query_embedding vector(768),
  match_threshold float default 0.0, -- Opcional
  match_count int default 10,        -- Opcional
  filter jsonb default '{}'          -- Opcional (LangChain costuma enviar)
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    memories.id,
    memories.content,
    memories.metadata,
    1 - (memories.embedding <=> query_embedding) as similarity
  from memories
  where 1 - (memories.embedding <=> query_embedding) > match_threshold
  order by memories.embedding <=> query_embedding
  limit match_count;
end;
$$;
