import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from combustivel import (  # noqa: E402
    Ambiente, AgenteDiaFixo, AgenteNivelMinimo, AgenteReativo, Config, Percepcao,
    passo_a_passo, resumir, simular,
)
from combustivel.formatacao import num  # noqa: E402
from combustivel.terminal import formatar_evento, formatar_resumo  # noqa: E402


class TestAmbiente(unittest.TestCase):
    def test_nivel_nunca_negativo_nem_acima_da_capacidade(self):
        cfg = Config(semente=1)
        _, amb = simular(AgenteReativo(cfg), cfg, dias=200)
        self.assertTrue(all(0 <= n <= cfg.capacidade_l for n in amb.historico_nivel))

    def test_abastecimento_limitado_ao_espaco_do_tanque(self):
        amb = Ambiente(Config(semente=3))
        amb.novo_dia()
        resultado_dia = amb.agir(litros=1000)  # tanque começa cheio
        self.assertEqual(resultado_dia.litros_abastecidos, 0.0)

    def test_reprodutibilidade_com_mesma_semente(self):
        cfg = Config(semente=7)
        r1, _ = simular(AgenteReativo(cfg), cfg, 40)
        r2, _ = simular(AgenteReativo(cfg), cfg, 40)
        self.assertEqual(r1.custo_total, r2.custo_total)

    def test_custo_e_soma_de_litros_vezes_preco(self):
        cfg = Config(semente=5)
        _, amb = simular(AgenteNivelMinimo(cfg), cfg, 60)
        esperado = sum(l * p for _, l, p in amb.abastecimentos)
        self.assertAlmostEqual(amb.custo_total, esperado)

    def test_tanque_seco_e_registrado(self):
        cfg = Config(capacidade_l=1.0, semente=2)  # tanque minúsculo
        resultado, _ = simular(AgenteDiaFixo(cfg, intervalo=1000), cfg, 10)
        self.assertGreater(resultado.dias_tanque_seco, 0)


class TestAgentes(unittest.TestCase):
    def setUp(self):
        self.cfg = Config()

    def test_reativo_abastece_com_nivel_baixo(self):
        agente = AgenteReativo(self.cfg)
        p = Percepcao(dia=1, preco=6.0, nivel=5.0, capacidade=50.0)
        decisao = agente.decidir(p)
        self.assertEqual(decisao.litros, 45.0)
        self.assertEqual(decisao.tipo, "urgencia")
        self.assertIn("Urgência", decisao.motivo)

    def test_reativo_nao_abastece_com_tanque_cheio_e_preco_normal(self):
        agente = AgenteReativo(self.cfg)
        p = Percepcao(dia=1, preco=6.0, nivel=45.0, capacidade=50.0)
        decisao = agente.decidir(p)
        self.assertEqual(decisao.litros, 0.0)
        self.assertFalse(decisao.abastece)
        self.assertTrue(decisao.motivo)

    def test_reativo_aproveita_preco_baixo(self):
        agente = AgenteReativo(self.cfg)
        for dia in range(1, 6):  # histórico de preços altos
            agente.decidir(Percepcao(dia=dia, preco=6.0, nivel=40.0, capacidade=50.0))
        p = Percepcao(dia=6, preco=5.0, nivel=25.0, capacidade=50.0)
        decisao = agente.decidir(p)
        self.assertEqual(decisao.litros, 25.0)
        self.assertEqual(decisao.tipo, "oportunidade")

    def test_dia_fixo(self):
        agente = AgenteDiaFixo(self.cfg, intervalo=7)
        self.assertEqual(agente.decidir(Percepcao(7, 6.0, 30.0, 50.0)).litros, 20.0)
        self.assertEqual(agente.decidir(Percepcao(8, 6.0, 30.0, 50.0)).litros, 0.0)


class TestAcompanhamento(unittest.TestCase):
    def setUp(self):
        self.cfg = Config(semente=42)

    def test_gerador_entrega_um_evento_por_dia(self):
        amb = Ambiente(self.cfg)
        eventos = list(passo_a_passo(AgenteReativo(self.cfg), amb, 30))
        self.assertEqual([e.dia for e in eventos], list(range(1, 31)))
        self.assertTrue(all(e.decisao.motivo for e in eventos))

    def test_custo_acumulado_final_bate_com_o_ambiente(self):
        amb = Ambiente(self.cfg)
        eventos = list(passo_a_passo(AgenteReativo(self.cfg), amb, 60))
        self.assertAlmostEqual(eventos[-1].custo_acumulado, amb.custo_total)
        self.assertAlmostEqual(sum(e.custo_dia for e in eventos), amb.custo_total)

    def test_gerador_e_simular_dao_o_mesmo_resultado(self):
        amb = Ambiente(self.cfg)
        for _ in passo_a_passo(AgenteReativo(self.cfg), amb, 60):
            pass
        r1 = resumir("x", amb)
        r2, _ = simular(AgenteReativo(self.cfg), self.cfg, 60)
        self.assertEqual(r1.custo_total, r2.custo_total)

    def test_resultado_da_semente_42_nao_mudou(self):
        # Garante que a refatoração não alterou o comportamento do agente
        r, _ = simular(AgenteReativo(self.cfg), self.cfg, 60)
        self.assertAlmostEqual(r.custo_total, 976.04, places=2)
        self.assertEqual(r.n_abastecimentos, 7)

    def test_formatacao_numerica_brasileira(self):
        self.assertEqual(num(1234.5), "1.234,50")
        self.assertEqual(num(5.0, 1), "5,0")

    def test_linha_do_terminal_mostra_decisao_e_motivo(self):
        amb = Ambiente(self.cfg)
        eventos = list(passo_a_passo(AgenteReativo(self.cfg), amb, 60))
        com = next(e for e in eventos if e.litros_abastecidos > 0)
        sem = next(e for e in eventos if e.litros_abastecidos == 0)
        self.assertIn("ABASTECE", formatar_evento(com, 60))
        self.assertIn(com.decisao.motivo, formatar_evento(com, 60))
        self.assertIn("sem abastecer", formatar_evento(sem, 60))

    def test_resumo_detalha_motivos_dos_abastecimentos(self):
        amb = Ambiente(self.cfg)
        eventos = list(passo_a_passo(AgenteReativo(self.cfg), amb, 60))
        texto = formatar_resumo(resumir("Reativo", amb), 60, eventos)
        self.assertIn("Abastecimentos", texto)
        self.assertIn("por oportunidade", texto)

    def test_gif_e_gerado(self):
        import matplotlib
        matplotlib.use("Agg")
        import tempfile
        from combustivel.visualizacao import salvar_gif
        amb = Ambiente(self.cfg)
        eventos = list(passo_a_passo(AgenteReativo(self.cfg), amb, 6))
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "teste.gif"
            salvar_gif(eventos, self.cfg, 6, caminho, fps=2, pausa_final_s=0.5)
            self.assertGreater(caminho.stat().st_size, 1000)
            self.assertEqual(caminho.read_bytes()[:3], b"GIF")


if __name__ == "__main__":
    unittest.main()
