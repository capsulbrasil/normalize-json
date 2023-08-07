# pyright: basic

from unittest import TestCase
from src.normalize_json.normalize import StringMapping, unserialize, translate_string

mapping1: StringMapping = {
  '__fields': {
    'created': '',
    'authorized': '',
    'waiting_payment': [
      'em análise',
      'aguardando pagamento',
      'pagamento atrasado',
      'em processamento'
    ],
    'paid': [
      'pagamento aprovado',
      'parcialmente pago'
    ],
    'handling_products': '',
    'on_carriage': '',
    'delivered': '',
    'cancelled': [
      'cancelada',
      'estorno pendente'
    ],
    'refused': '',
    'invoiced': '',
    'shipment_exception': 'devolvida',
    'chargeback': 'chargeback'
  }
}

class TestTranslateString(TestCase):
    def test_translate_string_output(self):
        self.assertEqual('paid', translate_string('pagamento aprovado', mapping1))
        self.assertEqual('paid', translate_string('parcialmente pago', mapping1))
        self.assertEqual('cancelled', translate_string('cancelada', mapping1))
        self.assertEqual('cancelled', translate_string('estorno pendente', mapping1))
        self.assertEqual(None, translate_string('unexisting', mapping1))
