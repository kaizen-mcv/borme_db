"""Tipos de actos mercantiles del BORME."""


class ACTO:
    """Actos mercantiles registrables."""
    NOMBRAMIENTOS = 1
    REVOCACIONES = 2
    CESES_DIMISIONES = 3
    MODIFICACIONES_ESTATUTARIAS = 4
    CAMBIO_DE_OBJETO_SOCIAL = 5
    CAMBIO_DE_DENOMINACION_SOCIAL = 6
    CAMBIO_DE_DOMICILIO_SOCIAL = 7
    AMPLIACION_DEL_OBJETO_SOCIAL = 8
    SOCIEDAD_UNIPERSONAL = 9
    DISOLUCION = 10
    REELECCIONES = 11
    CONSTITUCION = 12
    ARTICULO_378_5_DEL_RRM = 13
    OTROS_CONCEPTOS = 14
    AMPLIACION_DE_CAPITAL = 15
    REDUCCION_DE_CAPITAL = 16
    SITUACION_CONCURSAL = 17
    FUSION_POR_ABSORCION = 18
    SUSPENSION_DE_PAGOS = 19
    TRANSFORMACION_DE_SOCIEDAD = 20
    CANCELACIONES_DE_OFICIO_DE_NOMBRAMIENTOS = 21
    DESEMBOLSO_DE_DIVIDENDOS_PASIVOS = 22
    PAGINA_WEB_DE_LA_SOCIEDAD = 23
    PRIMERA_SUCURSAL_DE_SOCIEDAD_EXTRANJERA = 24
    EXTINCION = 26
    DECLARACION_DE_UNIPERSONALIDAD = 27
    PERDIDA_DEL_CARACTER_DE_UNIPERSONALIDAD = 28
    REAPERTURA_HOJA_REGISTRAL = 29
    ADAPTACION_LEY_2_95 = 30
    CIERRE_PROVISIONAL_BAJA_EN_EL_INDICE_DE_ENTIDADES_JURIDICAS = 31
    CIERRE_PROVISIONAL_REVOCACION_NIF = 32
    REACTIVACION_DE_LA_SOCIEDAD = 32
    FE_DE_ERRATAS = 34
    DATOS_REGISTRALES = 35
    CREDITO_INCOBRABLE = 36
    EMPRESARIO_INDIVIDUAL = 37
    EMISION_OBLIGACIONES = 38
    MODIFICACION_PODERES = 39
    ESCISION_PARCIAL = 40
    ESCISION_TOTAL = 41
    FUSION_UNION = 42
    ADAPTACION_DE_LA_SOCIEDAD = 43
    QUIEBRA = 44
    SUCURSAL = 45
    CESION_GLOBAL_ACTIVO_PASIVO = 46
    SEGREGACION = 47
    ACUERDO_AMPLIACION_CAPITAL_SOCIAL_SIN_EJECUTAR = 48
    MODIFICACION_DE_DURACION = 49
    APERTURA_DE_SUCURSAL = 50
    CIERRE_PROVISIONAL_IMPUESTO_SOCIEDADES = 51
    PRIMERA_INSCRIPCION = 52
    ANOTACION_PREVENTIVA_DEMANDA = 53
    ANOTACION_PREVENTIVA_DECLARACION = 54
    CIERRE_SUCURSAL = 55
    ADAPTACION_LEY_44_2015 = 56

    # Palabras clave con argumentos (cargos)
    ARG_KEYWORDS = [
        "Nombramientos",
        "Revocaciones",
        "Ceses/Dimisiones",
        "Modificaciones estatutarias",
        "Cambio de objeto social",
        "Cambio de denominación social",
        "Cambio de domicilio social",
        "Ampliacion del objeto social",
        "Disolución",
        "Reelecciones",
        "Constitución",
        "Apertura de sucursal",
        "Empresario Individual",
        "Articulo 378.5 del Reglamento del Registro Mercantil",
        "Otros conceptos",
        "Ampliación de capital",
        "Reducción de capital",
        "Situación concursal",
        "Fusión por absorción",
        "Suspensión de pagos",
        "Transformación de sociedad",
        "Cancelaciones de oficio de nombramientos",
        "Desembolso de dividendos pasivos",
        "Página web de la sociedad",
        "Primera sucursal de sociedad extranjera",
        "Emisión de obligaciones",
        "Modificación de poderes",
        "Escisión parcial",
        "Fusión por unión",
        "Quiebra",
        "Sucursal",
        "Cesión global de activo y pasivo",
        "Segregación",
        "Primera inscripcion (O.M. 10/6/1.997)",
        "Anotación preventiva. Demanda de impugnación de acuerdos sociales",
        "Anotación preventiva. Declaración de deudor fallido",
    ]

    # Palabras clave sin argumentos
    NOARG_KEYWORDS = [
        "Crédito incobrable",
        "Sociedad unipersonal",
        "Extinción",
        "Pérdida del caracter de unipersonalidad",
        "Reapertura hoja registral",
        "Adaptación Ley 2/95",
        "Adaptación Ley 44/2015",
        "Adaptada segun D.T. 2 apartado 2 Ley 2/95",
        "Cierre provisional hoja registral por baja en el índice de Entidades Jurídicas",
        "Cierre provisional de la hoja registral por revocación del NIF",
        "Cierre provisional hoja registral por revocación del NIFde Entidades Jurídicas",
        "Cierre provisional hoja registral art. 137.2 Ley 43/1995 Impuesto de Sociedades",
        "Reactivación de la sociedad (Art. 242 del Reglamento del Registro Mercantil)",
        "Adaptación de sociedad",
        "Cierre de Sucursal",
    ]

    # Palabras clave seguidas por :
    COLON_KEYWORDS = [
        "Modificación de duración",
        "Fe de erratas",
    ]

    # Palabras clave en negrita
    BOLD_KEYWORDS = [
        "Declaración de unipersonalidad",
        "Sociedad unipersonal",
        "Acuerdo de ampliación de capital social sin ejecutar. Importe del acuerdo",
        "Escisión total",
    ]

    # Palabra clave final
    ENDING_KEYWORDS = [
        "Datos registrales",
    ]

    ALL_KEYWORDS = ARG_KEYWORDS + NOARG_KEYWORDS + COLON_KEYWORDS + BOLD_KEYWORDS + ENDING_KEYWORDS


# Actos que implican cargos
ACTOS_CARGO = [
    "Revocaciones",
    "Reelecciones",
    "Cancelaciones de oficio de nombramientos",
    "Nombramientos",
    "Ceses/Dimisiones",
    "Emisión de obligaciones",
    "Modificación de poderes",
]

# Actos que aportan nuevos cargos (entrantes)
ACTOS_CARGO_ENTRANTE = ["Reelecciones", "Nombramientos"]
