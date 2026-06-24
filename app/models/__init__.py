# app/models/__init__.py

from .usuario import Usuario
from .paciente import Paciente
from .profissional_saude import ProfissionalSaude
from .administrador import Administrador

from .campanha import Campanha, CampanhaVacina
from .vacina import Vacina

from .lote import Lote
from .aplicacao import Aplicacao
from .document import Document