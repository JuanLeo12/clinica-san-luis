import sqlite3
import random

conn = sqlite3.connect('clinic_app.sqlite3')

# Datos de indicaciones por especialidad - incluyen restricciones y cuidados
especialidades_data = {
    1: {  # Medicina General
        'indicaciones': [
            'No autoadministrarse medicamentos sin receta. Evitar exposición al frió. Reposo relativo por 48 horas.',
            'No consumir alimentos picantes o muy condimentados. Evitar bebidas frías por 3 días.',
            'No realizar esfuerzos físicos intensos. Mantener hidratación abundanté. Evitar cambios bruscos de temperatura.',
            'Evitar lugares con humo o contaminación. No suspender el tratamiento aunque mejore. Seguir dosis exacta.',
            'No nadar ni mojar el área afectada. Evitar contacto con personas enfermas. Alimentación ligera.',
            'Lavarse las manos frecuentemente. No tocarse la cara. Usar mascarilla en lugares cerrados.',
            'Evitar lácteos si hay diarrea. No comer frituras. Dieta blanda por 3 días.',
            'No conducir vehículos si hay fiebre. Descansar en casa. Controlar temperatura cada 4 horas.'
        ]
    },
    2: {  # Pediatría
        'indicaciones': [
            'No dar aspirina a niños. Mantener al niño hidratado. Controlar fiebre cada 4 horas.',
            'Evitar exposición al sol directa. No vestir excesiva ropa al niño. Baños templados para bajar fiebre.',
            'No dar alimentos sólidos si hay vómitos. Suero oral cada 15 minutos. Dieta progresiva.',
            'Evitar contacto con animales. No usar juguetes pequeños. Supervisión constante del adulto.',
            'No dar leche de vaca si tiene diarrea. Dieta blanda. Aumentar líquidos.',
            'Mantener ventanas abiertas para ventilación. No exponer al humo. Humificador en habitación.',
            'Evitar juguetes pequeños que pueda tragar. No dejarlo solo cerca de objetos pequeños.',
            'No dar medicamentos sin supervisión médica. Observar cualquier reacción adversa.'
        ]
    },
    3: {  # Cardiología
        'indicaciones': [
            'No consumir sal en exceso. Evitar alimentos fritos. Controlar presión arterial diariamente.',
            'No realizar esfuerzos físicos intensos. Caminatas cortas許可idas. No levantar objetos pesados.',
            'Evitar emociones fuertes y estrés. No ver programas de tv intensos. Música relajante.',
            'No consumir cafeína ni alcohol. Dieta baja en grasas. Comer despacio.',
            'Evitar actividades que requieran esfuerzo. Descanso relativo. No subir escaleras.',
            'No fumar absolutamente. Evitar ambientes con humo. Caminatas suaves diariamente.',
            'Evitar clima frío extremo. Ropa abrigada. No exposition prolonged al eólica.',
            'No conducir si hay mareos. Controlar pulso regularmente. Escribir los resultados.'
        ]
    },
    4: {  # Dermatología
        'indicaciones': [
            'No rascarse las lesiones aunque piquen. Uñas cortas y limpias. Guantes de algodón en la noche.',
            'Evitar exposición solar directa. Usar bloqueador FPS 50+. Ropa protectora.',
            'No aplicar calor sobre las lesiones. Compresas frías. No usar bandas ajustadas.',
            'Evitar jabones agresivos. Usar jabón neutro. No restregar las lesiones.',
            'No compartir toallas ni ropa. No nadar en piscinas públicas. Ropa de algodón.',
            'Evitar alimentos que causen alergia (mariscos,坚果). Dieta sin picante. Mucha agua.',
            'No automedicarce con cremas. Solo medicamentos recetados. No cubrir las lesiones.',
            'Evitar duchas con agua muy caliente. Temperatura tibia. Secar sin friccionar.'
        ]
    },
    5: {  # Ginecología
        'indicaciones': [
            'No usar tampones, solo toallas sanitarias. Evitar baños de inmersión por 2 semanas.',
            'No tener relaciones sexuales por 2 semanas. No usar duchas vaginales.',
            'Evitar ejercicios de alto impacto por 1 semana. Descanso relativo. No levantar objetos pesados.',
            'No consumir bebidas con gas ni alcohólicas. Dieta rica en hierro.',
            'Evitar ropa ajustada. Usar ropa interior de algodón. No usar jeans muy tight.',
            'No exponerse al sol directamente. Evitar saunas. No bañarse en piscinas.',
            'No conducir bicicletas ni montar a caballo. Ejercicios suaves.',
            'Evitar estrés excesivo. Descansar apropiadamente. No tomar medicamentos sin consultar.'
        ]
    },
    6: {  # Traumatología
        'indicaciones': [
            'No apoyar la extremidad lesionada. Usar muletas si es necesario. No cargar peso.',
            'Evitar movimientos bruscos. No girar el cuerpo rápidamente. Movimientos lentos.',
            'No practicar deportes de contacto. No correr ni saltar. Caminar con cuidado.',
            'Evitar conducir vehículos. No manejar bicicleta. Descanso relativo.',
            'No dormir sobre el lado lesionado. Usar almohadas para elevar. Posición cómoda.',
            'Evitar cargar objetos pesados. No hacer fuerza. No agacharse bruscamente.',
            'No站立 por períodos largos. Sentarse regularmente. Elevar las piernas.',
            'Evitar superficies resbalosas. No caminar descalzo. Zapatos appropriate.'
        ]
    },
    7: {  # Oftalmología
        'indicaciones': [
            'No frotarse los ojos. No usar maquillaje por 1 semana. Lavar manos antes de tocarse.',
            'Evitar manejar de noche. No conducir con visión borrosa. Usar gafas de sol.',
            'No Swim ni salpicaduras de agua. Usar goggles. No abrir los ojos bajo el agua.',
            'Evitar pantallas por largos períodos. Descansar los ojos cada 20 minutos. Parpadeo frecuente.',
            'No usar lentes de contacto. Solo gafas. Limpieza diaria de gafas.',
            'Evitar ambientes con polvo. No salir en días muy windy. Usar gafas protectoras.',
            'No automedicarce gotas sin receta. Solo las recetadas. No compartir medicamentos.',
            'Evitar luz intensa directa. Usar lentes oscurecientes. Reducir brillo de pantallas.'
        ]
    },
    8: {  # Neurología
        'indicaciones': [
            'No conducir si hay mareos. No operar maquinaria. Descansar en lugar tranquilo.',
            'Evitar luces muy brillantes. No ver tv en cuarto oscuro. Persianas 半cerradas.',
            'No realizar actividades que requieran concentración intensa. Descansos frecuentes.',
            'Evitar estrés y emociones fuertes. No discusiones. Ambiente calmado.',
            'No dormir de día. Horario regular de sueño. No dormir más de 8 horas.',
            'Evitar alcohol absolutamente. No mezclar medicamentos con alcohol.',
            'No出去 sin accompany. Tener cuidador. No manejar solo.',
            'Evitar ruidos fuertes. Usar tapones. Ambiente silencioso.'
        ]
    },
    9: {  # Psiquiatría
        'indicaciones': [
            'No suspender medicación abruptamente. Seguir el traitement exactamente. No automedicar.',
            'Evitar alcohol y drogas. No mezclar con medicamentos. Abstinencia completa.',
            'No manejar vehículos maquinaria pesada. Riesgo de accidents. Esperar mejora.',
            'Evitar situaciones stressor. No confrontaciones. Ambiente familiares.',
            'No quedarse solo si hay ideas de autolesión. Apoyo permanente. Llamar ayuda.',
            'Evitar caffeína exceso. Cafeína limita. No energy drinks.',
            'No perubahan de rutinas abruptamente. Cambiosgraduales. Horario regular.',
            'Evitar isolation. Contacto social поддержка. Grupo de apoyo.'
        ]
    },
    10: {  # Otorrinolaringología
        'indicaciones': [
            'No sonarse la nariz con fuerza. Usar pañuelos suaves. Limpieza suave.',
            'Evitar ambientes con humo. No fumar. Ambientes libres de tabaco.',
            'No usar drops nasales por más de 5 días. Riesgo de efecto rebote. Consulta si persiste.',
            'Evitar piscinas y natatoria. No nadar. Agua puede contener bacterias.',
            'No consumir alimentos muy calientes o muy fríos. Temperatura moderada.',
            'Evitar cambios de presión (aviones, buceo). No viajes aéreos pending mejora.',
            'No gritar ni forzar la voz. Silencio relativo. Hablar poco.',
            'Evitar alergias conocido. No exposición a alérgenos. Purificador de aire.'
        ]
    },
    11: {  # Urología
        'indicaciones': [
            'No retener la orina por mucho tiempo. Orinar cada 3-4 horas. No esperar.',
            'Evitar bebidas con gas excesiva. Limitar caffeína. Mucha agua.',
            'No consumir alimentos muy especiados. Evitar picante. Dieta suave.',
            'Evitar riding bicicletas motorcycles por 2 semanas. Presión sobre prostata.',
            'No levantar objetos pesados. Presión abdominal. Evitar esfuerzo.',
            'Evitar alcohol especialmente cervezas. Empeora síntomas. Abstinencia.',
            'No usar ropa interior muy ajustada. Ropa suelta de algodón.',
            'Evitar frío extremo en zona lumbar. Ropa cálida. No sentorse en superficies frías.'
        ]
    },
    12: {  # Endocrinología
        'indicaciones': [
            'No saltarse comidas. Horario regular. No ayuno prolongado.',
            'Evitar azúcares simples. No dulces. Limitar carbohidratos.',
            'No realizar ejercicio intenso sin supervisión. Ejercicio moderado.',
            'Evitar estrés. Hormonas alteran glucosa. Técnicas de relajación.',
            'No modificar dosis de medicamentos solos. Siempre consultar.',
            'Evitar climate extremos. Temperatura estable. No exposición prolongada al frío/calor.',
            'No consumir alcohol. Alterna glucosa. Si consume, con moderación.',
            'Evitar infecciones. Lavado frecuente de manos. Prevenir heridas.'
        ]
    },
    13: {  # Neumología
        'indicaciones': [
            'No fumar absolutamente. Evitar ambientes con humo. Fumadores pasivos.',
            'No exponerse al polvo. Usar mascarilla. Ambiente limpio.',
            'No realizar exercise intenso. Ejercicio suave progresivo.',
            'Evitar frío y humedad. Ropa abrigada. No keluar بدون protección.',
            'No usar medicamentos sin supervisión. Algunos pueden interagir.',
            'Evitar lugares contaminación alta. Permanecer en casa si needed.',
            'No tener mascotas con pelo si es alérgico. Ambientes sin alérgenos.',
            'Evitar cambios temperatura bruscos. Aire acondicionado gradual.'
        ]
    },
    14: {  # Gastroenterología
        'indicaciones': [
            'No comer alimentos picantes. Evitar picante, frituras, grasa. Dieta blanda.',
            'No consumir alcohol absolut. Irrita la mucosa. Abstinencia.',
            'No comer en porciones grandes. Comidas pequeñas frecuentes.',
            'Evitar bebidas con gas. No refrescos. Agua natural.',
            'No乳制品 si hay intolerancia. Observar reacción. Evitar.',
            'No acostarse después de comer. Mantener posición erguida 2 horas.',
            'Evitar стресс. Técnicas de relajación. No comidas ansiosas.',
            'No automedicarce antiácidos. Uso prolongado requiere supervisión.'
        ]
    },
    15: {  # Reumatología
        'indicaciones': [
            'No realizar esfuerzos excesivos con las articulaciones afectadas. Descanso.',
            'Evitar frío intenso. Ropa cálida. No exposición prolonged al frío.',
            'No cargar objetos pesados. Usar carros para compras. No levantar.',
            'Evitar movimientos repetitivos. Descansos frecuentes. Rotar actividades.',
            'No subir escaleras frecuentemente. Evitar subir/bajar escalones.',
            'Evitar actividades de alto impacto. No correr. Caminar suavemente.',
            'Evitar humedad extrema. Ambiente seco. Deshumidificador.',
            'No dormir en posiciones que empeoren dolor. Almohadas para apoyar.'
        ]
    },
    16: {  # Angiología
        'indicaciones': [
            'No estar de pie por tiempos prolongados. Sentarse con piernas elevadas.',
            'No cruzar las piernas al sentarse. Mejor circulación. No presión.',
            'Evitar calcetines ajustados. No medias compresoras sin indicar. Ropa suelta.',
            'No caminar largos trayectos. Descansos frecuentes. No esfuerzo excesivo.',
            'Evitar heat excesivo en las piernas. No baños calientes. Compresas frías.',
            'No fumar absolutamente. Empeora circulación. Abstinencia total.',
            'Evitar alimentos altos en grasa. Dieta baja en colesterol.',
            'No usar zapatos apretados. Zapatos cómodos. No tacones altos.'
        ]
    },
}

print("=== ACTUALIZANDO INDICACIONES ===")

# Obtener todas las citas con sus especialidades
citas = conn.execute("""
    SELECT c.id, c.id_especialidad
    FROM citas c
    JOIN consultas con ON con.id_cita = c.id
    WHERE c.id_especialidad IS NOT NULL
""").fetchall()

print(f"Citas con especialidad: {len(citas)}")

actualizadas = 0

for cita in citas:
    id_cita = cita[0]
    id_esp = cita[1]

    if id_esp in especialidades_data:
        indicaciones = random.choice(especialidades_data[id_esp]['indicaciones'])

        conn.execute(
            "UPDATE consultas SET tratamiento = ? WHERE id_cita = ?",
            (indicaciones, id_cita)
        )
        actualizadas += 1

conn.commit()
print(f"Indicaciones actualizadas: {actualizadas}")

# Verificar algunas
muestras = conn.execute("""
    SELECT c.id_especialidad, con.tratamiento
    FROM consultas con
    JOIN citas c ON c.id = con.id_cita
    WHERE c.id_especialidad IN (1,2,3,4)
    LIMIT 8
""").fetchall()

print("\n=== MUESTRAS ===")
for m in muestras:
    print(f"Esp {m[0]}: {m[1][:60]}...")

conn.close()
print("\n¡Completado!")