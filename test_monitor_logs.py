import unittest 
from monitor_logs import contar_por_nivel, detectar_fuerza_bruta 

class TestMonitorLogs(unittest.TestCase): 

    def setUp(self): 
        self.eventos = [ 
            {"nivel": "ERROR",   "mensaje": "Intento de login fallido desde 10.0.0.1"}, 
            {"nivel": "ERROR",   "mensaje": "Intento de login fallido desde 10.0.0.1"}, 
            {"nivel": "ERROR",   "mensaje": "Intento de login fallido desde 10.0.0.1"}, 
            {"nivel": "WARNING", "mensaje": "Memoria alta"}, 
            {"nivel": "INFO",    "mensaje": "Servicio iniciado"}, 
        ] 

    def test_cuenta_total_por_nivel(self): 
        conteo = contar_por_nivel(self.eventos) 
        self.assertEqual(conteo["ERROR"], 3) # assertEqual: conteo["ERROR"] debe ser 3 

    def test_cuenta_warning_correcto(self): 
        conteo = contar_por_nivel(self.eventos) 
        self.assertEqual(conteo["WARNING"], 1) # assertEqual: conteo["WARNING"] debe ser 1 

    def test_detecta_ip_con_3_fallos(self): 
        sospechosas = detectar_fuerza_bruta(self.eventos, umbral=3) 
        self.assertIn("10.0.0.1", sospechosas) # assertIn: "10.0.0.1" debe estar en la lista 

    def test_no_detecta_con_pocos_fallos(self): 
        sospechosas = detectar_fuerza_bruta(self.eventos, umbral=5) 
        self.assertEqual(sospechosas, []) # assertEqual: la lista debe estar vacía [] 

    def test_eventos_info_no_generan_alerta(self): 
        solo_info = [e for e in self.eventos if e["nivel"] == "INFO"] 
        sospechosas = detectar_fuerza_bruta(solo_info) 
        self.assertEqual(sospechosas, []) # assertEqual con lista vacía 

if __name__ == "__main__": 
    unittest.main(verbosity=2)