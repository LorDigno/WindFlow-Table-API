from windflow_table_api.types import *

def run_factory_tests():
  print("=== AVVIO TEST TYPE FACTORY ===")

  # 1. Test risoluzione tipi scalari standard (case insensitive)
  t_int = TypeDescriptor.from_value("INT")
  assert t_int is DataTypes.INT
  assert t_int.cpp_type == "int32_t"
  assert t_int.is_number is True
  assert t_int.is_temporal is False
  print("✓ Risoluzione 'INT' superata.")

  t_double = TypeDescriptor.from_value("double")
  assert t_double is DataTypes.DOUBLE
  assert t_double.cpp_type == "double"
  assert t_double.is_number is True
  print("✓ Risoluzione 'double' (case-insensitive) superata.")

  # 2. Test caso limite: BOOL (value) vs BOOLEAN (name)
  t_bool_val = TypeDescriptor.from_value("BOOL")
  t_bool_name = TypeDescriptor.from_value("BOOLEAN")
  assert t_bool_val is DataTypes.BOOLEAN
  assert t_bool_name is DataTypes.BOOLEAN
  assert t_bool_val.is_boolean is True
  assert t_bool_val.cpp_type == "bool"
  print("✓ Risoluzione 'BOOL' e 'BOOLEAN' superata.")

  # 3. Test formati temporali (con e senza prefisso TIMESTAMP_)
  t_iso = TypeDescriptor.from_value("ISO8601")
  assert t_iso is TimeFormats.ISO8601
  assert t_iso.cpp_type == "uint64_t"
  assert t_iso.is_temporal is True
  assert t_iso.is_number is False
  print("✓ Risoluzione 'ISO8601' superata.")

  # 4. Test Idempotenza (passare un'istanza già risolta)
  original_type = DataTypes.BIGINT
  resolved = TypeDescriptor.from_value(original_type)
  assert resolved is original_type
  print("✓ Idempotenza da istanza esistente superata.")

  # 5. Test chiamata specializzata su sottoclasse
  dt_only = DataTypes.from_value("INT")
  assert dt_only is DataTypes.INT

  try:
    # DataTypes.from_value("ISO8601") deve fallire perché non appartiene a DataTypes
    DataTypes.from_value("ISO8601")
    assert False, "Avrebbe dovuto sollevare ValueError"
  except ValueError:
    print("✓ Restrizione per sottoclasse (DataTypes su ISO8601) superata.")

  # 6. Test tipi non validi
  try:
    TypeDescriptor.from_value("TIPO_INESISTENTE")
    assert False, "Avrebbe dovuto sollevare ValueError"
  except ValueError as e:
    print(f"✓ Errore intercettato su tipo sconosciuto: {e}")

  try:
    TypeDescriptor.from_value(12345)  # type: ignore
    assert False, "Avrebbe dovuto sollevare TypeError"
  except TypeError as e:
    print(f"✓ Errore intercettato su input non stringa: {e}")

  print("\n TUTTI I TEST SONO STATI SUPERATI CON SUCCESSO!")


if __name__ == "__main__":
  run_factory_tests()