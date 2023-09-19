from typing import NamedTuple
from urllib.parse import quote
from textwrap import dedent
from .piso import Piso


class Mail(NamedTuple):
    to: str
    subject: str
    body: str

    def to_url(self):
        return "".join([
            'mailto:',
            self.to,
            '?',
            'subject=',
            quote(self.subject),
            '&',
            'body=',
            quote(self.body)
        ])

    @staticmethod
    def askInfo(p: Piso):
        to = dict(
            sia='SIA@emvs.es',
            alq='info@planalquila.org'
        )[p.plan]
        return Mail(
            to=to,
            subject=f'Piso {p.id}',
            body=dedent(f'''
                Hola

                Me interesa el piso nº {p.id}, ubicado en {p.get_direccion()} ({p.zona}).

                Por favor, ¿pueden decirme como concertar una visita y obtener información adicional?

                Gracias.
                Un saludo.
            ''').strip()
        )
