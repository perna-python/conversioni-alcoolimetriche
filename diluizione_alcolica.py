"""Calcoli alcoolimetrici basati su densità della miscela etanolo-acqua a 20 °C."""

from dataclasses import dataclass

DENSITA_PER_PESO = {
    0: 0.99823, 1: 0.99636, 2: 0.99453, 3: 0.99275, 4: 0.99103,
    5: 0.98938, 6: 0.98780, 7: 0.98627, 8: 0.98478, 9: 0.98331,
    10: 0.98187, 11: 0.98047, 12: 0.97910, 13: 0.97775, 14: 0.97643,
    15: 0.97514, 16: 0.97387, 17: 0.97259, 18: 0.97129, 19: 0.96997,
    20: 0.96864, 21: 0.96729, 22: 0.96592, 23: 0.96453, 24: 0.96312,
    25: 0.96168, 26: 0.96020, 27: 0.95867, 28: 0.95710, 29: 0.95548,
    30: 0.95382, 31: 0.95212, 32: 0.95038, 33: 0.94860, 34: 0.94679,
    35: 0.94494, 36: 0.94306, 37: 0.94114, 38: 0.93919, 39: 0.93720,
    40: 0.93518, 41: 0.93314, 42: 0.93107, 43: 0.92897, 44: 0.92685,
    45: 0.92472, 46: 0.92257, 47: 0.92041, 48: 0.91823, 49: 0.91604,
    50: 0.91384, 51: 0.91160, 52: 0.90936, 53: 0.90711, 54: 0.90485,
    55: 0.90258, 56: 0.90031, 57: 0.89803, 58: 0.89574, 59: 0.89344,
    60: 0.89113, 61: 0.88882, 62: 0.88650, 63: 0.88417, 64: 0.88183,
    65: 0.87948, 66: 0.87713, 67: 0.87477, 68: 0.87241, 69: 0.87004,
    70: 0.86766, 71: 0.86527, 72: 0.86287, 73: 0.86047, 74: 0.85806,
    75: 0.85564, 76: 0.85322, 77: 0.85079, 78: 0.84835, 79: 0.84590,
    80: 0.84344, 81: 0.84096, 82: 0.83848, 83: 0.83599, 84: 0.83348,
    85: 0.83095, 86: 0.82840, 87: 0.82583, 88: 0.82323, 89: 0.82062,
    90: 0.81797, 91: 0.81529, 92: 0.81257, 93: 0.80983, 94: 0.80705,
    95: 0.80424, 96: 0.80138, 97: 0.79846, 98: 0.79547, 99: 0.79243,
    100: 0.78934,
}

RHO_ETANOLO_PURO = DENSITA_PER_PESO[100]
RHO_ACQUA_20C = DENSITA_PER_PESO[0]


def densita_da_peso(percento_peso: float) -> float:
    if percento_peso <= 0:
        return DENSITA_PER_PESO[0]
    if percento_peso >= 100:
        return DENSITA_PER_PESO[100]
    inf = int(percento_peso)
    sup = inf + 1
    frazione = percento_peso - inf
    return DENSITA_PER_PESO[inf] + frazione * (DENSITA_PER_PESO[sup] - DENSITA_PER_PESO[inf])


def volume_percento_da_peso(percento_peso: float) -> float:
    return percento_peso * densita_da_peso(percento_peso) / RHO_ETANOLO_PURO


def peso_da_volume_percento(percento_volume: float, tolleranza: float = 1e-6) -> float:
    basso, alto = 0.0, 100.0
    while alto - basso > tolleranza:
        medio = (basso + alto) / 2
        if volume_percento_da_peso(medio) < percento_volume:
            basso = medio
        else:
            alto = medio
    return (basso + alto) / 2


@dataclass
class RisultatoDiluizione:
    acqua_da_aggiungere_ml: float
    acqua_da_aggiungere_g: float
    volume_alcol_partenza_ml: float
    volume_finale_ml: float
    massa_finale_g: float
    grado_partenza_vv: float
    grado_target_vv: float


def acqua_da_aggiungere(volume_alcol_partenza_ml: float, grado_target_vv: float, grado_partenza_vv: float = 96.0) -> RisultatoDiluizione:
    w_partenza = peso_da_volume_percento(grado_partenza_vv)
    w_target = peso_da_volume_percento(grado_target_vv)
    if w_target >= w_partenza:
        raise ValueError(f"Il grado target ({grado_target_vv}°) deve essere inferiore al grado di partenza ({grado_partenza_vv}°).")
    rho_partenza = densita_da_peso(w_partenza)
    massa_partenza = volume_alcol_partenza_ml * rho_partenza
    massa_etanolo_puro = massa_partenza * (w_partenza / 100)
    massa_finale = massa_etanolo_puro / (w_target / 100)
    massa_acqua = massa_finale - massa_partenza
    volume_acqua_ml = massa_acqua / RHO_ACQUA_20C
    rho_finale = densita_da_peso(w_target)
    volume_finale_ml = massa_finale / rho_finale
    return RisultatoDiluizione(round(volume_acqua_ml, 2), round(massa_acqua, 2), round(volume_alcol_partenza_ml, 2), round(volume_finale_ml, 2), round(massa_finale, 2), grado_partenza_vv, grado_target_vv)


def diluizione_per_massa_finale(massa_finale_g: float, grado_target_vv: float, grado_partenza_vv: float = 96.0) -> dict:
    w_partenza = peso_da_volume_percento(grado_partenza_vv)
    w_target = peso_da_volume_percento(grado_target_vv)
    if w_target >= w_partenza:
        raise ValueError(f"Il grado target ({grado_target_vv}°) deve essere inferiore al grado di partenza ({grado_partenza_vv}°).")
    massa_etanolo_target = massa_finale_g * (w_target / 100)
    massa_alcol_partenza_g = massa_etanolo_target / (w_partenza / 100)
    massa_acqua_g = massa_finale_g - massa_alcol_partenza_g
    return {
        "massa_alcol_partenza_g": round(massa_alcol_partenza_g, 2),
        "massa_acqua_g": round(massa_acqua_g, 2),
        "massa_finale_g": round(massa_finale_g, 2),
        "grado_partenza_vv": grado_partenza_vv,
        "grado_target_vv": grado_target_vv,
        "percento_m_m_partenza": round(w_partenza, 2),
        "percento_m_m_target": round(w_target, 2),
    }


def diluizione_per_volume_finale(volume_finale_ml: float, grado_target_vv: float, grado_partenza_vv: float = 96.0) -> dict:
    w_partenza = peso_da_volume_percento(grado_partenza_vv)
    w_target = peso_da_volume_percento(grado_target_vv)
    if w_target >= w_partenza:
        raise ValueError(f"Il grado target ({grado_target_vv}°) deve essere inferiore al grado di partenza ({grado_partenza_vv}°).")
    rho_target = densita_da_peso(w_target)
    massa_finale = volume_finale_ml * rho_target
    massa_etanolo_puro = massa_finale * (w_target / 100)
    rho_partenza = densita_da_peso(w_partenza)
    massa_alcol_partenza = massa_etanolo_puro / (w_partenza / 100)
    volume_alcol_partenza_ml = massa_alcol_partenza / rho_partenza
    massa_acqua = massa_finale - massa_alcol_partenza
    volume_acqua_ml = massa_acqua / RHO_ACQUA_20C
    return {
        "volume_alcol_partenza_ml": round(volume_alcol_partenza_ml, 2),
        "acqua_da_aggiungere_ml": round(volume_acqua_ml, 2),
        "acqua_da_aggiungere_g": round(massa_acqua, 2),
        "volume_finale_ml": round(volume_finale_ml, 2),
        "massa_finale_g": round(massa_finale, 2),
    }
