-- Schema usado pelos testes de integração.
-- Origem: `mysqldump --no-data` do banco real (Dump20261112.sql).
-- ATENÇÃO: este arquivo é uma cópia. Quando o schema do banco real mudar,
-- gere o dump de novo e atualize este arquivo, senão os testes passam
-- contra um banco diferente do de produção.

DROP TABLE IF EXISTS `reservas`;
DROP TABLE IF EXISTS `salas`;
DROP TABLE IF EXISTS `usuarios`;

CREATE TABLE `salas` (
  `id_sala` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `capacidade` tinyint unsigned NOT NULL,
  `predio` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `andar` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status_sala` enum('Disponivel','Indisponivel','Manutencao') COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo_sala` enum('Sala','Reuniao','Auditorio','Laboratorio') COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_sala`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `usuarios` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(320) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefone` varchar(11) COLLATE utf8mb4_unicode_ci NOT NULL,
  `papel` enum('Aluno','Professor','Admin') COLLATE utf8mb4_unicode_ci NOT NULL,
  `senha` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status_usuario` enum('Ativo','Inativo') COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `reservas` (
  `id_reserva` int NOT NULL AUTO_INCREMENT,
  `id_usuario` int NOT NULL,
  `id_sala` int NOT NULL,
  `data_reserva` date NOT NULL,
  `hora_inicio` time NOT NULL,
  `hora_fim` time NOT NULL,
  `status_reserva` enum('Confirmada','Pendente','Cancelada') COLLATE utf8mb4_unicode_ci NOT NULL,
  `criado_em` date NOT NULL,
  PRIMARY KEY (`id_reserva`),
  KEY `id_usuario` (`id_usuario`),
  KEY `id_sala` (`id_sala`),
  CONSTRAINT `reservas_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`),
  CONSTRAINT `reservas_ibfk_2` FOREIGN KEY (`id_sala`) REFERENCES `salas` (`id_sala`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
