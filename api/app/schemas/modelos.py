from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, AfterValidator

TextoSede = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200
    )
]

class SedeEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: TextoSede
    direccion: TextoSede
    ciudad: TextoSede
    capacidad_maxima: int = Field(gt=0, strict=True)
    servicios_disponibles: list[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=80
            )
        ]
    ] = Field(default_factory=list, max_length=20)

from typing import Self
from pydantic import AwareDatetime, model_validator

TextoActividad = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=150
    )
]

class ActividadBaseEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo_actividad: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=20
        )
    ]
    titulo: TextoActividad
    orador: TextoActividad
    sala: TextoActividad
    inicio: AwareDatetime
    fin: AwareDatetime

    @model_validator(mode="after")
    def validar_horario(self) -> Self:
        if self.fin <= self.inicio:
            raise ValueError(
                "El fin de la actividad debe ser posterior al inicio."
            )
        return self

from typing import Literal

TextoDetalle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=300
    )
]

class DetallesTaller(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requiere_notebook: bool = False
    software_previo: list[TextoDetalle] = Field(
        default_factory=list,
        max_length=10
    )
    nivel: TextoDetalle | None = None


class DetallesConferencia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transmision_streaming: bool = False
    url_streaming: TextoDetalle | None = None
    traduccion_simultanea: bool = False

    @model_validator(mode="after")
    def validar_transmision(self) -> Self:
        if self.transmision_streaming and not self.url_streaming:
            raise ValueError(
                "Una conferencia con streaming debe indicar su URL."
            )
        return self


class DetallesPanel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    moderador: TextoDetalle | None = None
    panelistas: list[TextoDetalle] = Field(
        default_factory=list,
        max_length=10
    )


class TallerEntrada(ActividadBaseEntrada):
    tipo: Literal["taller"]
    detalles_especificos: DetallesTaller = Field(
        default_factory=DetallesTaller
    )


class ConferenciaEntrada(ActividadBaseEntrada):
    tipo: Literal["conferencia"]
    detalles_especificos: DetallesConferencia = Field(
        default_factory=DetallesConferencia
    )


class PanelEntrada(ActividadBaseEntrada):
    tipo: Literal["panel"]
    detalles_especificos: DetallesPanel = Field(
        default_factory=DetallesPanel
    )


ActividadEntrada = Annotated[
    TallerEntrada | ConferenciaEntrada | PanelEntrada,
    Field(discriminator="tipo")
]

from decimal import Decimal

TextoEvento = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=150
    )
]

TextoEtiqueta = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=40
    )
]


def normalizar_conocimiento(valor: str) -> str:
    valor = valor.strip().lower()
    if not valor:
        raise ValueError("Un conocimiento no puede estar vacio.")
    return valor

Conocimiento = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=80),
    AfterValidator(normalizar_conocimiento)
]

def sin_repetidos(valores: list[str]) -> list[str]:
    return list(dict.fromkeys(valores))

Conocimientos = Annotated[
    list[Conocimiento], Field(max_length=50), AfterValidator(sin_repetidos)
]

class EventoCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conocimientos_requeridos: Conocimientos = Field(default_factory=list)

    titulo: TextoEvento
    categoria: TextoEvento
    fecha_inicio: AwareDatetime
    fecha_fin: AwareDatetime

    precio_entrada: Decimal = Field(
        ge=0,
        decimal_places=2,
        allow_inf_nan=False
    )

    capacidad_total: int = Field(gt=0, strict=True)
    sede: SedeEntrada

    actividades: list[ActividadEntrada] = Field(
        min_length=1,
        max_length=30
    )

    etiquetas: list[TextoEtiqueta] = Field(
        default_factory=list,
        max_length=20
    )

    requisitos_generales: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=1000
        )
    ] | None = None

    @model_validator(mode="after")
    def validar_evento(self) -> Self:
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError(
                "El fin del evento debe ser posterior al inicio."
            )

        if self.capacidad_total > self.sede.capacidad_maxima:
            raise ValueError(
                "La capacidad del evento supera la capacidad de la sede."
            )

        codigos = [
            actividad.codigo_actividad
            for actividad in self.actividades
        ]

        if len(codigos) != len(set(codigos)):
            raise ValueError(
                "Los codigos de actividad no pueden repetirse."
            )

        for actividad in self.actividades:
            if (
                actividad.inicio < self.fecha_inicio
                or actividad.fin > self.fecha_fin
            ):
                raise ValueError(
                    "Las actividades deben estar dentro del horario del evento."
                )

        if len(self.etiquetas) != len(set(self.etiquetas)):
            raise ValueError(
                "Las etiquetas no pueden repetirse."
            )

        return self

class EventoActualizar(BaseModel):
    conocimientos_requeridos: Conocimientos | None = None

    model_config = ConfigDict(extra="forbid")

    titulo: TextoEvento | None = None
    categoria: TextoEvento | None = None

    precio_entrada: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        allow_inf_nan=False
    )

    capacidad_total: int | None = Field(
        default=None,
        gt=0,
        strict=True
    )

    estado: Literal["publicado"] | None = None

    @model_validator(mode="after")
    def validar_cambios(self) -> Self:
        if not self.model_fields_set:
            raise ValueError(
                "Debe indicar al menos un campo para actualizar."
            )

        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError(
                    f"El campo {campo} no puede ser null."
                )

        return self

class FiltrosEventos(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limite: int = Field(default=20, ge=1, le=100)
    categoria: TextoEvento | None = None

    estado: Literal[
        "borrador", "publicado", "finalizado", "cancelado"
    ] | None = None

    ciudad: TextoSede | None = None
    conocimiento: Conocimiento | None = None
    con_vacantes: bool = False
    etiqueta: TextoEtiqueta | None = None

    fecha_desde: AwareDatetime | None = None
    fecha_hasta: AwareDatetime | None = None

    precio_minimo: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        allow_inf_nan=False
    )

    precio_maximo: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        allow_inf_nan=False
    )

    @model_validator(mode="after")
    def validar_intervalos(self) -> Self:
        if (
            self.fecha_desde is not None
            and self.fecha_hasta is not None
            and self.fecha_hasta <= self.fecha_desde
        ):
            raise ValueError(
                "fecha_hasta debe ser posterior a fecha_desde."
            )

        if (
            self.precio_minimo is not None
            and self.precio_maximo is not None
            and self.precio_maximo < self.precio_minimo
        ):
            raise ValueError(
                "El precio maximo no puede ser menor que el minimo."
            )

        return self

from pydantic import EmailStr

TextoUsuario = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=150
    )
]

class UsuarioEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre_completo: TextoUsuario

    dni: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=20,
            pattern=r"^[0-9]+$"
        )
    ]

    email: EmailStr

    conocimientos: Conocimientos = Field(default_factory=list)

    institucion: TextoUsuario | None = None


class InscripcionCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario: UsuarioEntrada
    tipo_entrada: Literal["general", "invitacion"] = "general"

    metodo_pago: Literal[
        "efectivo", "transferencia"
    ] | None = None

    actividades_seleccionadas: list[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=20
            )
        ]
    ] = Field(default_factory=list, max_length=30)

    preferencias_alimentarias: list[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=80
            )
        ]
    ] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validar_seleccion(self) -> Self:
        codigos = self.actividades_seleccionadas

        if len(codigos) != len(set(codigos)):
            raise ValueError(
                "No se puede seleccionar la misma actividad dos veces."
            )

        return self
