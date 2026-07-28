-- Listar todas as tarefas
SELECT * FROM tasks;

-- Mostrar apenas tarefas concluídas
SELECT * FROM tasks WHERE done = 1;

-- Contar todas as tarefas
SELECT COUNT(*) FROM tasks;

-- Marcar todas as tarefas como concluídas
UPDATE tasks SET done = 1;

-- Excluir todas as tarefas concluídas
DELETE FROM tasks WHERE done = 1;
