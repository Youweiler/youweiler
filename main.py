import flet as ft
import json
import os
import smtplib
import random
import qrcode
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================
# CONFIGURACION
# ==============================================
CORREO_REMITENTE = "Ricky.tb.94@gmail.com"
CONTRASENA_APP = "jpxdjbgocewptsom"
COLOR_FONDO = "#f0f4f8"
COLOR_PRIMARIO = "#2c7a7b"
COLOR_SECUNDARIO = "#38b2ac"
COLOR_TEXTO = "#2d3748"

recuperacion_tokens = {}

def obtener_ruta_datos(page: ft.Page):
    # Usar el directorio de documentos seguro de la aplicación en móviles (iOS/Android)
    base_dir = page.get_persistent_storage_path() if page.platform in [ft.PagePlatform.IOS, ft.PagePlatform.ANDROID] else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "usuarios_youweiler.json")

def cargar_datos(page: ft.Page):
    try:
        ruta = obtener_ruta_datos(page)
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando datos: {e}")
    return {}

def guardar_datos(page: ft.Page, datos):
    try:
        ruta = obtener_ruta_datos(page)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2)
    except Exception as e:
        print(f"Error guardando datos: {e}")

def calcular_edad(mes_nac, anio_nac):
    ahora = datetime.now()
    anios = ahora.year - anio_nac
    meses = ahora.month - mes_nac
    if meses < 0:
        anios -= 1
        meses += 12
    return anios, meses

def generar_codigo_6digitos():
    return str(random.randint(100000, 999999))

def enviar_correo_generico(destino, asunto, cuerpo):
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = CORREO_REMITENTE
        mensaje["To"] = destino
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))
        servidor = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        servidor.login(CORREO_REMITENTE, CONTRASENA_APP)
        servidor.sendmail(CORREO_REMITENTE, destino, mensaje.as_string())
        servidor.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

# ==============================================
# INTERFAZ FLET
# ==============================================
def main(page: ft.Page):
    page.title = "YOUWEILER 🐾"
    page.bgcolor = COLOR_FONDO
    page.padding = 20
    page.window_width = 380
    page.window_height = 700

    usuario_actual = ""
    codigo_secreto = ""
    correo_temporal = ""

    def limpiar():
        page.clean()
        page.update()

    def pantalla_inicio():
        limpiar()
        page.add(
            ft.Column([
                ft.Text("YOUWEILER", size=32, weight="bold", color=COLOR_PRIMARIO),
                ft.Text("Clinica Veterinaria", size=16, color=COLOR_TEXTO),
                ft.Divider(height=30),
                ft.ElevatedButton("Iniciar Sesion", on_click=lambda e: pantalla_login(),
                                  bgcolor=COLOR_PRIMARIO, color="white", width=300),
                ft.ElevatedButton("Registrarse", on_click=lambda e: pantalla_registro_paso1(),
                                  bgcolor=COLOR_SECUNDARIO, color="white", width=300),
                ft.TextButton("Salir", on_click=lambda e: page.window_close())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_login():
        limpiar()
        nonlocal usuario_actual

        correo_input = ft.TextField(label="Correo o usuario", width=320)
        clave_input = ft.TextField(label="Contrasena", password=True, width=320)
        mensaje_error = ft.Text("", color="red")

        def entrar(e):
            nonlocal usuario_actual
            datos = cargar_datos(page)
            usuario_buscar = correo_input.value.strip().lower()
            encontrado = None
            for u in datos:
                if u.lower() == usuario_buscar or datos[u].get("correo", "").lower() == usuario_buscar:
                    encontrado = u
                    break
            if encontrado and datos[encontrado]["contrasena"] == clave_input.value:
                usuario_actual = encontrado
                pantalla_menu()
            else:
                mensaje_error.value = "Usuario o contrasena incorrectos"
                page.update()

        clave_input.on_submit = entrar

        page.add(
            ft.Column([
                ft.Text("Iniciar Sesion", size=22, weight="bold", color=COLOR_PRIMARIO),
                correo_input,
                clave_input,
                mensaje_error,
                ft.ElevatedButton("Entrar", on_click=entrar, bgcolor=COLOR_PRIMARIO, color="white", width=320),
                ft.TextButton("Olvido su contrasena?", on_click=lambda e: pantalla_recuperar()),
                ft.TextButton("Volver", on_click=lambda e: pantalla_inicio())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_recuperar():
        limpiar()
        correo_input = ft.TextField(label="Correo registrado", width=320)

        def enviar_codigo(e):
            nonlocal codigo_secreto
            correo = correo_input.value.strip().lower()
            datos = cargar_datos(page)
            usuario_encontrado = None
            for u in datos:
                if datos[u].get("correo", "").lower() == correo:
                    usuario_encontrado = u
                    break
            if not usuario_encontrado:
                page.add(ft.Text("No existe ese correo", color="red"))
                page.update()
                return
            codigo = generar_codigo_6digitos()
            recuperacion_tokens[codigo] = usuario_encontrado
            cuerpo = f"Tu código de recuperación es: {codigo}"
            enviado = enviar_correo_generico(correo, "Recuperar contraseña - YOUWEILER", cuerpo)
            if not enviado:
                page.add(ft.Text(f"Código: {codigo}", color="orange"))
            codigo_secreto = codigo
            pantalla_nueva_clave(usuario_encontrado)

        page.add(
            ft.Column([
                ft.Text("Recuperar Contraseña", size=20, weight="bold", color=COLOR_PRIMARIO),
                correo_input,
                ft.ElevatedButton("Enviar código", on_click=enviar_codigo, bgcolor=COLOR_PRIMARIO, color="white", width=320),
                ft.TextButton("Volver", on_click=lambda e: pantalla_login())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_nueva_clave(usuario):
        limpiar()
        clave1 = ft.TextField(label="Nueva contraseña", password=True, width=320)
        clave2 = ft.TextField(label="Repetir contraseña", password=True, width=320)

        def guardar(e):
            if len(clave1.value) < 4:
                page.add(ft.Text("Mínimo 4 caracteres", color="red"))
                page.update()
                return
            if clave1.value != clave2.value:
                page.add(ft.Text("No coinciden", color="red"))
                page.update()
                return
            datos = cargar_datos(page)
            datos[usuario]["contrasena"] = clave1.value
            guardar_datos(page, datos)
            pantalla_login()

        page.add(
            ft.Column([
                ft.Text("Nueva Contraseña", size=20, weight="bold", color=COLOR_PRIMARIO),
                clave1, clave2,
                ft.ElevatedButton("Guardar", on_click=guardar, bgcolor=COLOR_PRIMARIO, color="white", width=320)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_registro_paso1():
        nonlocal correo_temporal
        limpiar()
        correo_input = ft.TextField(label="Correo electrónico", width=320)

        def enviar(e):
            nonlocal codigo_secreto, correo_temporal
            correo = correo_input.value.strip().lower()
            if "@" not in correo or "." not in correo:
                page.add(ft.Text("Correo inválido", color="red"))
                page.update()
                return
            datos = cargar_datos(page)
            existe = any(datos[u].get("correo", "").lower() == correo for u in datos)
            if existe:
                page.add(ft.Text("Este correo ya está registrado", color="red"))
                page.update()
                return
            codigo_secreto = generar_codigo_6digitos()
            enviado = enviar_correo_generico(correo, "Verificación - YOUWEILER", f"Tu código: {codigo_secreto}")
            if not enviado:
                page.add(ft.Text(f"Código: {codigo_secreto}", color="orange"))
            correo_temporal = correo
            pantalla_registro_paso2()

        page.add(
            ft.Column([
                ft.Text("Registro - Paso 1", size=20, weight="bold", color=COLOR_PRIMARIO),
                correo_input,
                ft.ElevatedButton("Enviar código", on_click=enviar, bgcolor=COLOR_PRIMARIO, color="white", width=320),
                ft.TextButton("Volver", on_click=lambda e: pantalla_inicio())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_registro_paso2():
        limpiar()
        codigo_input = ft.TextField(label="Código de 6 dígitos", width=320)

        def verificar(e):
            if codigo_input.value.strip() == codigo_secreto:
                pantalla_registro_paso3()
            else:
                page.add(ft.Text("Código incorrecto", color="red"))
                page.update()

        page.add(
            ft.Column([
                ft.Text("Verificar Código", size=20, weight="bold", color=COLOR_PRIMARIO),
                codigo_input,
                ft.ElevatedButton("Verificar", on_click=verificar, bgcolor=COLOR_PRIMARIO, color="white", width=320),
                ft.TextButton("Volver", on_click=lambda e: pantalla_registro_paso1())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_registro_paso3():
        nonlocal correo_temporal
        limpiar()
        usuario_input = ft.TextField(label="Nombre de usuario", width=320)
        clave1 = ft.TextField(label="Contraseña", password=True, width=320)
        clave2 = ft.TextField(label="Repetir contraseña", password=True, width=320)

        def crear_cuenta(e):
            usuario = usuario_input.value.strip()
            if len(usuario) < 2:
                page.add(ft.Text("Usuario muy corto", color="red"))
                page.update()
                return
            if clave1.value != clave2.value or len(clave1.value) < 4:
                page.add(ft.Text("Contraseñas no coinciden o muy cortas", color="red"))
                page.update()
                return
            datos = cargar_datos(page)
            if usuario.lower() in datos:
                page.add(ft.Text("Usuario ya existe", color="red"))
                page.update()
                return
            datos[usuario.lower()] = {
                "correo": correo_temporal,
                "contrasena": clave1.value,
                "mascotas": {}
            }
            guardar_datos(page, datos)
            pantalla_login()

        page.add(
            ft.Column([
                ft.Text("Crear Cuenta", size=20, weight="bold", color=COLOR_PRIMARIO),
                usuario_input,
                clave1,
                clave2,
                ft.ElevatedButton("Completar registro", on_click=crear_cuenta, bgcolor=COLOR_PRIMARIO, color="white", width=320),
                ft.TextButton("Volver", on_click=lambda e: pantalla_registro_paso2())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_menu():
        limpiar()
        page.add(
            ft.Column([
                ft.Text(f"Bienvenido, {usuario_actual}! 🐾", size=22, weight="bold", color=COLOR_PRIMARIO),
                ft.Divider(height=20),
                ft.ElevatedButton("Ver mis mascotas", on_click=lambda e: pantalla_mascotas(), width=300, bgcolor=COLOR_PRIMARIO, color="white"),
                ft.ElevatedButton("Agregar nueva mascota", on_click=lambda e: pantalla_agregar_mascota(), width=300, bgcolor=COLOR_SECUNDARIO, color="white"),
                ft.ElevatedButton("Cerrar sesión", on_click=lambda e: pantalla_inicio(), width=300, bgcolor="#e2e8f0", color=COLOR_TEXTO)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_mascotas():
        limpiar()
        datos = cargar_datos(page)
        usuario_datos = datos.get(usuario_actual, {})
        mascotas = usuario_datos.get("mascotas", {})
        elementos = []

        if not mascotas:
            elementos.append(ft.Text("Aún no tienes mascotas registradas", size=16, color=COLOR_TEXTO))
        else:
            for nombre, info in mascotas.items():
                edad_txt = ""
                if "mes_nac" in info and "anio_nac" in info:
                    a, m = calcular_edad(info["mes_nac"], info["anio_nac"])
                    edad_txt = f"Edad: {a}a {m}m"
                elementos.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"🐾 {nombre}", size=16, weight="bold", color=COLOR_PRIMARIO),
                            ft.Text(f"{info.get('especie', '')} - {info.get('raza', '')}  |  Peso: {info.get('peso', '')} kg"),
                            ft.Text(edad_txt),
                            ft.Text(f"📍 {info.get('direccion', 'No registrada')}"),
                            ft.Text(f"📞 {info.get('celular', 'No registrado')}"),
                            ft.ElevatedButton("Ver ficha completa", 
                                              on_click=lambda e, n=nombre: pantalla_ficha(n), width=250)
                        ]),
                        padding=15, bgcolor="white", border_radius=10
                    )
                )

        elementos.append(ft.TextButton("Volver al menú", on_click=lambda e: pantalla_menu()))
        page.add(
            ft.Column([
                ft.Text("Mis Mascotas", size=24, weight="bold", color=COLOR_PRIMARIO),
                *elementos
            ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def pantalla_ficha(nombre_mascota):
        limpiar()
        try:
            datos = cargar_datos(page)
            mascotas = datos.get(usuario_actual, {}).get("mascotas", {})
            info = mascotas.get(nombre_mascota, {})

            if not info:
                page.add(ft.Text("Mascota no encontrada", color="red"))
                page.add(ft.TextButton("Volver", on_click=lambda e: pantalla_mascotas()))
                page.update()
                return

            especie = info.get("especie", "No registrada")
            raza = info.get("raza", "No registrada")
            peso = info.get("peso", "No registrado")
            direccion = info.get("direccion", "No registrada")
            celular = info.get("celular", "No registrado")
            foto_ruta = info.get("foto", "")

            mes_nac = info.get("mes_nac")
            anio_nac = info.get("anio_nac")
            if mes_nac and anio_nac:
                anios, meses = calcular_edad(mes_nac, anio_nac)
                edad_texto = f"Edad: {anios} anos y {meses} meses"
            else:
                edad_texto = "Edad: No disponible"

            foto_container = ft.Container(
                width=150, height=150,
                bgcolor="#e2e8f0",
                border_radius=75,
                alignment=ft.alignment.center,
                content=ft.Text("Sin foto", size=12, color="#718096")
            )
            if foto_ruta and os.path.exists(foto_ruta):
                foto_container.content = ft.Image(src=foto_ruta, width=150, height=150, fit=ft.ImageFit.COVER)

            qr_container = ft.Container(visible=False)

            def on_file_picked(e):
                if e.files:
                    ruta_seleccionada = e.files[0].path
                    datos_actualizados = cargar_datos(page)
                    datos_actualizados[usuario_actual]["mascotas"][nombre_mascota]["foto"] = ruta_seleccionada
                    guardar_datos(page, datos_actualizados)
                    foto_container.content = ft.Image(src=ruta_seleccionada, width=150, height=150, fit=ft.ImageFit.COVER)
                    page.update()

            file_picker = ft.FilePicker(on_result=on_file_picked)
            page.overlay.append(file_picker)

            def seleccionar_foto(e):
                file_picker.pick_files(
                    allow_multiple=False,
                    allowed_extensions=["png", "jpg", "jpeg", "webp"]
                )

            def generar_qr(e):
                try:
                    contenido = (
                        f"YOUWEILER - Ficha de Mascota\n"
                        f"Nombre: {nombre_mascota}\n"
                        f"Especie: {especie}\n"
                        f"Raza: {raza}\n"
                        f"Direccion: {direccion}\n"
                        f"Celular: {celular}"
                    )
                    qr_imagen = qrcode.make(contenido)
                    
                    # Guardar temporalmente en el directorio de la app
                    temp_dir = page.get_persistent_storage_path() if page.platform in [ft.PagePlatform.IOS, ft.PagePlatform.ANDROID] else os.path.dirname(os.path.abspath(__file__))
                    ruta_qr = os.path.join(temp_dir, f"QR_{usuario_actual}_{nombre_mascota}.png")
                    qr_imagen.save(ruta_qr)

                    with open(ruta_qr, "rb") as f:
                        imagen_bytes = f.read()

                    qr_container.content = ft.Column([
                        ft.Text("Tu Codigo QR:", weight="bold", size=16),
                        ft.Image(src=imagen_bytes, width=220, height=220, fit=ft.ImageFit.CONTAIN),
                        ft.Text("Guardado correctamente", size=10, color="green")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    qr_container.visible = True
                    page.update()
                except Exception as err:
                    page.add(ft.Text(f"Error QR: {err}", color="red"))
                    page.update()

            vacunas_lista = info.get("vacunas", [])
            vacunas_texto = "\n".join([f"• {v.get('vacuna', '—')} | {v.get('fecha', '—')}" for v in vacunas_lista]) if vacunas_lista else "Sin vacunas registradas"

            historial_lista = info.get("historial", [])
            historial_texto = "\n".join([f"• {c.get('fecha', '—')} | {c.get('motivo', '—')}" for c in historial_lista]) if historial_lista else "Sin consultas registradas"

            page.add(
                ft.Column([
                    foto_container,
                    ft.ElevatedButton("Agregar / Cambiar foto", on_click=seleccionar_foto,
                                      bgcolor=COLOR_SECUNDARIO, color="white", width=250),
                    ft.Divider(),
                    ft.Text(nombre_mascota, size=26, weight="bold", color=COLOR_PRIMARIO),
                    ft.Text(f"{especie}  •  {raza}"),
                    ft.Text(f"{edad_texto}  |  Peso: {peso} kg"),
                    ft.Divider(),
                    ft.Text(f"📍 Dirección: {direccion}"),
                    ft.Text(f"📞 Celular: {celular}"),
                    ft.Divider(),
                    ft.Text("💉 Vacunas:", weight="bold"),
                    ft.Text(vacunas_texto),
                    ft.Divider(),
                    ft.Text("🏥 Historial:", weight="bold"),
                    ft.Text(historial_texto),
                    ft.Divider(),
                    ft.ElevatedButton("📱 Generar Codigo QR", on_click=generar_qr, bgcolor="#805ad5", color="white", width=300),
                    qr_container,
                    ft.TextButton("Volver", on_click=lambda e: pantalla_mascotas())
                ], scroll=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
            page.update()
        except Exception as e:
            page.add(ft.Text(f"Error: {e}", color="red"))
            page.add(ft.TextButton("Volver", on_click=lambda e: pantalla_mascotas()))
            page.update()

    def pantalla_agregar_mascota():
        limpiar()
        nom = ft.TextField(label="Nombre", width=320)
        esp = ft.TextField(label="Especie", width=320)
        raz = ft.TextField(label="Raza", width=320)
        pes = ft.TextField(label="Peso (kg)", width=320)
        dir_ = ft.TextField(label="Direccion", width=320)
        cel = ft.TextField(label="Celular", width=320)
        mes = ft.TextField(label="Mes nacimiento (1-12)", width=320)
        anio = ft.TextField(label="Anio nacimiento", width=320)
        mensaje = ft.Text("", color="red")

        def guardar_mascota(e):
            if not nom.value or not esp.value or not raz.value or not pes.value:
                mensaje.value = "Completa los campos obligatorios"
                page.update()
                return
            try:
                m_val = int(mes.value)
                a_val = int(anio.value)
                if not (1 <= m_val <= 12):
                    mensaje.value = "Mes invalido (1-12)"
                    page.update()
                    return
            except:
                mensaje.value = "Mes y ano deben ser numeros"
                page.update()
                return

            datos = cargar_datos(page)
            nombre_nuevo = nom.value.strip()

            if usuario_actual not in datos:
                datos[usuario_actual] = {"mascotas": {}}
            if "mascotas" not in datos[usuario_actual]:
                datos[usuario_actual]["mascotas"] = {}

            if nombre_nuevo in datos[usuario_actual]["mascotas"]:
                mensaje.value = "Ya existe una mascota con ese nombre"
                page.update()
                return

            datos[usuario_actual]["mascotas"][nombre_nuevo] = {
                "especie": esp.value.strip(),
                "raza": raz.value.strip(),
                "peso": pes.value.strip(),
                "direccion": dir_.value.strip(),
                "celular": cel.value.strip(),
                "mes_nac": m_val,
                "anio_nac": a_val,
                "foto": "",
                "vacunas": [],
                "historial": []
            }
            guardar_datos(page, datos)
            pantalla_menu()

        page.add(
            ft.Column([
                ft.Text("Agregar Nueva Mascota", size=22, weight="bold", color=COLOR_PRIMARIO),
                nom, esp, raz, pes, dir_, cel, mes, anio,
                mensaje,
                ft.ElevatedButton("Guardar Mascota", on_click=guardar_mascota, bgcolor=COLOR_PRIMARIO, color="white", width=320),
                ft.TextButton("Volver", on_click=lambda e: pantalla_menu())
            ], scroll=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    pantalla_inicio()

if __name__ == "__main__":
    ft.app(target=main)