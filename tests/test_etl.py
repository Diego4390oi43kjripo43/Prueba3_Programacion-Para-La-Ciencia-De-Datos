"""
test_etl.py — Tests automatizados del pipeline ETL
Ejecutar: pytest tests/ -v
SCY1101 EP3 | Accidentes de Tráfico España 2024
"""
import sys, pytest, pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.extract_csv import transformar_accidentes
from etl.extract_api import _datos_respaldo
from etl.validate    import validar_columnas, validar_rangos, reporte_calidad


# ══════════════════════════════════════════════════════════════
# TESTS: extract_csv.py
# ══════════════════════════════════════════════════════════════

class TestTransformacion:

    def test_tramo_hora_existe(self, df_muestra):
        """La transformación debe crear la columna TRAMO_HORA."""
        resultado = transformar_accidentes(df_muestra)
        assert 'TRAMO_HORA' in resultado.columns

    def test_tramo_hora_valores_correctos(self):
        """Cada hora debe mapearse al tramo correcto."""
        df = pd.DataFrame({
            'HORA': [3, 8, 14, 22],
            'MES': [1]*4, 'DIA_SEMANA': [1]*4,
            'TOTAL_VICTIMAS_24H': [0]*4, 'TOTAL_VEHICULOS': [1]*4,
            'CONDICION_METEO': [1]*4, 'CONDICION_ILUMINACION': [1]*4,
            'CONDICION_FIRME': [1]*4, 'TRAZADO_PLANTA': [1]*4,
            'HAY_NIEBLA': [0]*4, 'TIPO_VIA': [1]*4, 'TIPO_ACCIDENTE': [1]*4,
        })
        r = transformar_accidentes(df)
        assert r.iloc[0]['TRAMO_HORA'] == 'Madrugada'
        assert r.iloc[1]['TRAMO_HORA'] == 'Mañana'
        assert r.iloc[2]['TRAMO_HORA'] == 'Tarde'
        assert r.iloc[3]['TRAMO_HORA'] == 'Noche'

    def test_gravedad_existe(self, df_muestra):
        """La transformación debe crear la columna gravedad_accidente."""
        resultado = transformar_accidentes(df_muestra)
        assert 'gravedad_accidente' in resultado.columns

    def test_gravedad_valores_permitidos(self, df_muestra):
        """gravedad_accidente debe contener solo Baja, Media, Alta o nan."""
        resultado = transformar_accidentes(df_muestra)
        permitidos = {'Baja', 'Media', 'Alta', 'nan'}
        valores_unicos = set(resultado['gravedad_accidente'].unique())
        assert valores_unicos.issubset(permitidos)

    def test_nulos_rellenos_hay_niebla(self, df_con_nulos):
        """HAY_NIEBLA no debe tener nulos después de transformar."""
        resultado = transformar_accidentes(df_con_nulos)
        assert resultado['HAY_NIEBLA'].isna().sum() == 0

    def test_nulos_rellenos_victimas(self, df_con_nulos):
        """TOTAL_VICTIMAS_24H no debe tener nulos después de transformar."""
        resultado = transformar_accidentes(df_con_nulos)
        assert resultado['TOTAL_VICTIMAS_24H'].isna().sum() == 0

    def test_shape_conservado(self, df_muestra):
        """La transformación no debe cambiar el número de filas."""
        resultado = transformar_accidentes(df_muestra)
        assert len(resultado) == len(df_muestra)

    def test_columnas_originales_presentes(self, df_muestra):
        """Todas las columnas originales deben seguir presentes."""
        resultado = transformar_accidentes(df_muestra)
        for col in df_muestra.columns:
            assert col in resultado.columns


# ══════════════════════════════════════════════════════════════
# TESTS: extract_api.py
# ══════════════════════════════════════════════════════════════

class TestExtractAPI:

    def test_respaldo_12_filas(self):
        """Los datos de respaldo deben tener 12 registros (meses)."""
        df = _datos_respaldo()
        assert len(df) == 12

    def test_respaldo_columnas(self):
        """Los datos de respaldo deben tener las columnas requeridas."""
        df = _datos_respaldo()
        assert 'MES' in df.columns
        assert 'precipitacion_media_mm' in df.columns
        assert 'temp_max_media_c' in df.columns
        assert 'viento_max_media_kmh' in df.columns

    def test_respaldo_meses_rango(self):
        """Los meses en los datos de respaldo deben ir de 1 a 12."""
        df = _datos_respaldo()
        assert df['MES'].min() == 1
        assert df['MES'].max() == 12

    def test_respaldo_sin_nulos(self):
        """Los datos de respaldo no deben tener nulos."""
        df = _datos_respaldo()
        assert df.isnull().sum().sum() == 0


# ══════════════════════════════════════════════════════════════
# TESTS: validate.py
# ══════════════════════════════════════════════════════════════

class TestValidacion:

    def test_columnas_valido_con_dataset_completo(self, df_muestra):
        """Debe retornar válido cuando todas las columnas existen."""
        resultado = validar_columnas(df_muestra)
        assert resultado['valido'] is True

    def test_columnas_invalido_falta_columna(self, df_muestra):
        """Debe detectar columnas faltantes."""
        df_incompleto = df_muestra.drop(columns=['HORA', 'MES'])
        resultado = validar_columnas(df_incompleto)
        assert resultado['valido'] is False
        assert 'HORA' in resultado['columnas_faltantes']
        assert 'MES' in resultado['columnas_faltantes']

    def test_rangos_validos_dataset_correcto(self, df_muestra):
        """Dataset correcto debe pasar validación de rangos."""
        resultado = validar_rangos(df_muestra)
        assert resultado['valido'] is True

    def test_rangos_invalidos_hora(self):
        """Debe detectar horas fuera del rango 0-23."""
        df = pd.DataFrame({
            'HORA': [25, 30], 'MES': [1, 2], 'DIA_SEMANA': [1, 2],
            'TOTAL_VICTIMAS_24H': [0, 1], 'TOTAL_VEHICULOS': [1, 2],
            'CONDICION_METEO': [1, 1], 'CONDICION_ILUMINACION': [1, 1],
            'CONDICION_FIRME': [1, 1], 'TRAZADO_PLANTA': [1, 1],
            'HAY_NIEBLA': [0, 0], 'TIPO_VIA': [1, 1], 'TIPO_ACCIDENTE': [1, 1],
        })
        resultado = validar_rangos(df)
        assert resultado['valido'] is False
        assert 'HORA' in resultado['errores_por_columna']

    def test_reporte_calidad_keys(self, df_muestra):
        """El reporte de calidad debe contener todas las claves esperadas."""
        reporte = reporte_calidad(df_muestra)
        assert 'total_registros' in reporte
        assert 'total_columnas' in reporte
        assert 'duplicados' in reporte
        assert 'porcentaje_nulos_total' in reporte

    def test_reporte_total_registros_correcto(self, df_muestra):
        """El total de registros debe coincidir con el DataFrame."""
        reporte = reporte_calidad(df_muestra)
        assert reporte['total_registros'] == len(df_muestra)
