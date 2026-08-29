"""Pruebas unitarias de autorización, parsing y validación de herramientas."""

import unittest

from tools import consultar_estado_sistema, ejecutar_herramienta, obtener_sla


class ToolTests(unittest.TestCase):
    """Verifica la frontera que separa texto del modelo y ejecución de Python."""

    def test_sla_alta(self) -> None:
        """Confirma el dato controlado para una criticidad válida."""
        self.assertEqual(obtener_sla("alta")["sla_horas"], 4)

    def test_criticidad_desconocida(self) -> None:
        """Confirma que una etiqueta fuera del dominio no produce un SLA inventado."""
        self.assertEqual(obtener_sla("urgente")["estado"], "error")

    def test_sistema_desconocido(self) -> None:
        """Confirma que una fuente sin registro responde con incertidumbre explícita."""
        resultado = consultar_estado_sistema("facturacion_internacional")
        self.assertEqual(resultado["estado"], "desconocido")

    def test_herramienta_no_autorizada(self) -> None:
        """Confirma que el despachador rechaza funciones fuera de la lista permitida."""
        resultado = ejecutar_herramienta("borrar_base", "{}")
        self.assertEqual(resultado["tipo"], "herramienta_no_autorizada")

    def test_json_invalido(self) -> None:
        """Confirma que texto malformado del modelo no llega a una función real."""
        resultado = ejecutar_herramienta("obtener_sla", "{")
        self.assertEqual(resultado["tipo"], "json_invalido")

    def test_propiedad_adicional(self) -> None:
        """Confirma que el contrato estricto rechaza argumentos inesperados."""
        resultado = ejecutar_herramienta(
            "obtener_sla", '{"criticidad":"alta","extra":1}'
        )
        self.assertEqual(resultado["tipo"], "validacion")


if __name__ == "__main__":
    unittest.main()
