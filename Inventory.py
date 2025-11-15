"""
============================================================
SISTEMA DE INVENTARIO COMPLETO - TODO EN UN ARCHIVO
============================================================
Guarda este archivo como: inventario.py
Ejecuta: python inventario.py
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime


# ============================================================
# CLASES DEL MODELO
# ============================================================

class Producto:
    def __init__(self, codigo, nombre, precio_compra, precio_venta, 
                 stock_actual, stock_minimo, categoria, id_producto=None):
        
        if not codigo or str(codigo).strip() == "":
            raise ValueError("El código no puede estar vacío")
        if not nombre or str(nombre).strip() == "":
            raise ValueError("El nombre no puede estar vacío")
        if float(precio_compra) < 0:
            raise ValueError("El precio de compra no puede ser negativo")
        if float(precio_venta) < 0:
            raise ValueError("El precio de venta no puede ser negativo")
        if int(stock_actual) < 0:
            raise ValueError("El stock actual no puede ser negativo")
        if int(stock_minimo) < 0:
            raise ValueError("El stock mínimo no puede ser negativo")
        if not categoria or str(categoria).strip() == "":
            raise ValueError("La categoría no puede estar vacía")
        
        self.id_producto = id_producto
        self.codigo = str(codigo).strip()
        self.nombre = str(nombre).strip()
        self.precio_compra = float(precio_compra)
        self.precio_venta = float(precio_venta)
        self.stock_actual = int(stock_actual)
        self.stock_minimo = int(stock_minimo)
        self.categoria = str(categoria).strip()
    
    def necesita_reabastecimiento(self):
        return self.stock_actual <= self.stock_minimo


class Movimiento:
    def __init__(self, tipo, producto_codigo, producto_nombre, cantidad, 
                 responsable, motivo=None, fecha=None, id_movimiento=None):
        
        if tipo not in ["ENTRADA", "SALIDA", "DEVOLUCION", "PERDIDA"]:
            raise ValueError("Tipo inválido")
        if int(cantidad) <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        if not responsable or str(responsable).strip() == "":
            raise ValueError("El responsable no puede estar vacío")
        if tipo in ["DEVOLUCION", "PERDIDA"] and (not motivo or str(motivo).strip() == ""):
            raise ValueError("El motivo es obligatorio")
        
        self.id_movimiento = id_movimiento
        self.fecha = fecha if fecha else datetime.now()
        self.tipo = tipo
        self.producto_codigo = producto_codigo
        self.producto_nombre = producto_nombre
        self.cantidad = int(cantidad)
        self.responsable = str(responsable).strip()
        self.motivo = str(motivo).strip() if motivo else None


# ============================================================
# BASE DE DATOS
# ============================================================

class BD:
    def __init__(self, archivo="inventario.db"):
        self.archivo = archivo
        self.crear_tablas()
    
    def conectar(self):
        return sqlite3.connect(self.archivo)
    
    def crear_tablas(self):
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                precio_compra REAL NOT NULL,
                precio_venta REAL NOT NULL,
                stock_actual INTEGER NOT NULL,
                stock_minimo INTEGER NOT NULL,
                categoria TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                tipo TEXT NOT NULL,
                producto_codigo TEXT NOT NULL,
                producto_nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                responsable TEXT NOT NULL,
                motivo TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def guardar_producto(self, producto):
        conn = self.conectar()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO productos (codigo, nombre, precio_compra, precio_venta, 
                                     stock_actual, stock_minimo, categoria)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (producto.codigo, producto.nombre, producto.precio_compra,
                  producto.precio_venta, producto.stock_actual, 
                  producto.stock_minimo, producto.categoria))
            
            cursor.execute('INSERT OR IGNORE INTO categorias (nombre) VALUES (?)', 
                         (producto.categoria,))
            
            conn.commit()
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Ya existe ese código"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def obtener_producto(self, codigo):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM productos WHERE codigo = ?', (codigo,))
        fila = cursor.fetchone()
        conn.close()
        
        if fila:
            return Producto(
                codigo=fila[1], nombre=fila[2], precio_compra=fila[3],
                precio_venta=fila[4], stock_actual=fila[5],
                stock_minimo=fila[6], categoria=fila[7], id_producto=fila[0]
            )
        return None
    
    def obtener_todos_productos(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM productos ORDER BY codigo')
        filas = cursor.fetchall()
        conn.close()
        
        productos = []
        for fila in filas:
            productos.append(Producto(
                codigo=fila[1], nombre=fila[2], precio_compra=fila[3],
                precio_venta=fila[4], stock_actual=fila[5],
                stock_minimo=fila[6], categoria=fila[7], id_producto=fila[0]
            ))
        return productos
    
    def actualizar_producto(self, producto):
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE productos 
            SET nombre=?, precio_compra=?, precio_venta=?, 
                stock_actual=?, stock_minimo=?, categoria=?
            WHERE codigo=?
        ''', (producto.nombre, producto.precio_compra, producto.precio_venta,
              producto.stock_actual, producto.stock_minimo, producto.categoria,
              producto.codigo))
        
        conn.commit()
        filas = cursor.rowcount
        conn.close()
        return filas > 0
    
    def eliminar_producto(self, codigo):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM productos WHERE codigo = ?', (codigo,))
        conn.commit()
        filas = cursor.rowcount
        conn.close()
        return filas > 0
    
    def buscar_productos(self, criterio, valor):
        conn = self.conectar()
        cursor = conn.cursor()
        
        if criterio == 'codigo':
            cursor.execute('SELECT * FROM productos WHERE codigo = ?', (valor,))
        elif criterio == 'nombre':
            cursor.execute('SELECT * FROM productos WHERE nombre LIKE ?', (f'%{valor}%',))
        elif criterio == 'categoria':
            cursor.execute('SELECT * FROM productos WHERE categoria = ?', (valor,))
        else:
            conn.close()
            return []
        
        filas = cursor.fetchall()
        conn.close()
        
        productos = []
        for fila in filas:
            productos.append(Producto(
                codigo=fila[1], nombre=fila[2], precio_compra=fila[3],
                precio_venta=fila[4], stock_actual=fila[5],
                stock_minimo=fila[6], categoria=fila[7], id_producto=fila[0]
            ))
        return productos
    
    def guardar_movimiento(self, movimiento):
        conn = self.conectar()
        cursor = conn.cursor()
        
        fecha_str = movimiento.fecha.strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO movimientos (fecha, tipo, producto_codigo, producto_nombre,
                                   cantidad, responsable, motivo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (fecha_str, movimiento.tipo, movimiento.producto_codigo,
              movimiento.producto_nombre, movimiento.cantidad,
              movimiento.responsable, movimiento.motivo))
        
        conn.commit()
        id_mov = cursor.lastrowid
        conn.close()
        return id_mov
    
    def obtener_movimientos(self, limite=None):
        conn = self.conectar()
        cursor = conn.cursor()
        
        if limite:
            cursor.execute('SELECT * FROM movimientos ORDER BY fecha DESC LIMIT ?', (limite,))
        else:
            cursor.execute('SELECT * FROM movimientos ORDER BY fecha DESC')
        
        filas = cursor.fetchall()
        conn.close()
        
        movimientos = []
        for fila in filas:
            fecha = datetime.strptime(fila[1], "%Y-%m-%d %H:%M:%S")
            movimientos.append(Movimiento(
                tipo=fila[2], producto_codigo=fila[3], producto_nombre=fila[4],
                cantidad=fila[5], responsable=fila[6], motivo=fila[7],
                fecha=fecha, id_movimiento=fila[0]
            ))
        return movimientos
    
    def obtener_movimientos_por_tipo(self, tipo, limite=None):
        conn = self.conectar()
        cursor = conn.cursor()
        
        if limite:
            cursor.execute('SELECT * FROM movimientos WHERE tipo = ? ORDER BY fecha DESC LIMIT ?', 
                         (tipo, limite))
        else:
            cursor.execute('SELECT * FROM movimientos WHERE tipo = ? ORDER BY fecha DESC', (tipo,))
        
        filas = cursor.fetchall()
        conn.close()
        
        movimientos = []
        for fila in filas:
            fecha = datetime.strptime(fila[1], "%Y-%m-%d %H:%M:%S")
            movimientos.append(Movimiento(
                tipo=fila[2], producto_codigo=fila[3], producto_nombre=fila[4],
                cantidad=fila[5], responsable=fila[6], motivo=fila[7],
                fecha=fecha, id_movimiento=fila[0]
            ))
        return movimientos
    
    def eliminar_ultimo_movimiento(self):
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM movimientos ORDER BY id DESC LIMIT 1')
        fila = cursor.fetchone()
        
        if not fila:
            conn.close()
            return None
        
        fecha = datetime.strptime(fila[1], "%Y-%m-%d %H:%M:%S")
        movimiento = Movimiento(
            tipo=fila[2], producto_codigo=fila[3], producto_nombre=fila[4],
            cantidad=fila[5], responsable=fila[6], motivo=fila[7],
            fecha=fecha, id_movimiento=fila[0]
        )
        
        cursor.execute('DELETE FROM movimientos WHERE id = ?', (fila[0],))
        conn.commit()
        conn.close()
        return movimiento
    
    def obtener_categorias(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('SELECT nombre FROM categorias ORDER BY nombre')
        filas = cursor.fetchall()
        conn.close()
        return [fila[0] for fila in filas]


# ============================================================
# GESTOR DE INVENTARIO
# ============================================================

class Gestor:
    def __init__(self):
        self.bd = BD()
    
    def agregar_producto(self, producto, responsable="Sistema"):
        if not isinstance(producto, Producto):
            return False, "Error: Debe ser un Producto"
        
        exito, resultado = self.bd.guardar_producto(producto)
        
        if not exito:
            return False, f"Error: {resultado}"
        
        if producto.stock_actual > 0:
            mov = Movimiento("ENTRADA", producto.codigo, producto.nombre,
                           producto.stock_actual, responsable)
            self.bd.guardar_movimiento(mov)
        
        return True, f"Producto {producto.nombre} agregado"
    
    def modificar_producto(self, codigo, **kwargs):
        producto = self.bd.obtener_producto(codigo)
        if not producto:
            return False, "Producto no encontrado"
        
        if 'nombre' in kwargs and kwargs['nombre']:
            producto.nombre = kwargs['nombre']
        if 'precio_compra' in kwargs and kwargs['precio_compra'] >= 0:
            producto.precio_compra = kwargs['precio_compra']
        if 'precio_venta' in kwargs and kwargs['precio_venta'] >= 0:
            producto.precio_venta = kwargs['precio_venta']
        if 'stock_minimo' in kwargs and kwargs['stock_minimo'] >= 0:
            producto.stock_minimo = kwargs['stock_minimo']
        if 'categoria' in kwargs and kwargs['categoria']:
            producto.categoria = kwargs['categoria']
        
        if self.bd.actualizar_producto(producto):
            return True, "Producto actualizado"
        return False, "Error al actualizar"
    
    def eliminar_producto(self, codigo):
        producto = self.bd.obtener_producto(codigo)
        if not producto:
            return False, "Producto no encontrado"
        
        if self.bd.eliminar_producto(codigo):
            return True, f"Producto {producto.nombre} eliminado"
        return False, "Error al eliminar"
    
    def buscar_producto(self, criterio, valor):
        return self.bd.buscar_productos(criterio, valor)
    
    def listar_productos(self):
        return self.bd.obtener_todos_productos()
    
    def registrar_entrada(self, codigo, cantidad, responsable="Sistema"):
        producto = self.bd.obtener_producto(codigo)
        if not producto:
            return False, "Producto no encontrado"
        
        producto.stock_actual += int(cantidad)
        self.bd.actualizar_producto(producto)
        
        mov = Movimiento("ENTRADA", codigo, producto.nombre, cantidad, responsable)
        self.bd.guardar_movimiento(mov)
        
        return True, f"Entrada: +{cantidad} de {producto.nombre}"
    
    def registrar_salida(self, codigo, cantidad, responsable="Sistema"):
        producto = self.bd.obtener_producto(codigo)
        if not producto:
            return False, "Producto no encontrado"
        
        if producto.stock_actual < cantidad:
            return False, f"Stock insuficiente: {producto.stock_actual}"
        
        producto.stock_actual -= int(cantidad)
        self.bd.actualizar_producto(producto)
        
        mov = Movimiento("SALIDA", codigo, producto.nombre, cantidad, responsable)
        self.bd.guardar_movimiento(mov)
        
        return True, f"Salida: -{cantidad} de {producto.nombre}"
    
    def registrar_devolucion(self, codigo, cantidad, motivo, responsable="Sistema"):
        producto = self.bd.obtener_producto(codigo)
        if not producto:
            return False, "Producto no encontrado"
        
        producto.stock_actual += int(cantidad)
        self.bd.actualizar_producto(producto)
        
        mov = Movimiento("DEVOLUCION", codigo, producto.nombre, cantidad, responsable, motivo)
        self.bd.guardar_movimiento(mov)
        
        return True, f"Devolución: +{cantidad} de {producto.nombre}"
    
    def registrar_perdida(self, codigo, cantidad, tipo_perdida, motivo, responsable="Sistema"):
        producto = self.bd.obtener_producto(codigo)
        if not producto:
            return False, "Producto no encontrado"
        
        if producto.stock_actual < cantidad:
            return False, f"Stock insuficiente: {producto.stock_actual}"
        
        producto.stock_actual -= int(cantidad)
        self.bd.actualizar_producto(producto)
        
        motivo_completo = f"[{tipo_perdida.upper()}] {motivo}"
        mov = Movimiento("PERDIDA", codigo, producto.nombre, cantidad, responsable, motivo_completo)
        self.bd.guardar_movimiento(mov)
        
        return True, f"Pérdida: -{cantidad} de {producto.nombre}"
    
    def productos_con_stock_bajo(self):
        todos = self.bd.obtener_todos_productos()
        return [p for p in todos if p.necesita_reabastecimiento()]
    
    def obtener_historial(self, limite=None):
        return self.bd.obtener_movimientos(limite)
    
    def obtener_devoluciones(self, limite=None):
        return self.bd.obtener_movimientos_por_tipo("DEVOLUCION", limite)
    
    def obtener_perdidas(self, tipo_filtro=None):
        perdidas = self.bd.obtener_movimientos_por_tipo("PERDIDA")
        if tipo_filtro:
            return [p for p in perdidas if p.motivo and tipo_filtro.upper() in p.motivo]
        return perdidas
    
    def calcular_perdidas_totales(self):
        perdidas_por_tipo = {
            'robo': {'cantidad': 0, 'valor': 0},
            'merma': {'cantidad': 0, 'valor': 0},
            'caducidad': {'cantidad': 0, 'valor': 0},
            'daño': {'cantidad': 0, 'valor': 0}
        }
        
        perdidas = self.bd.obtener_movimientos_por_tipo("PERDIDA")
        
        for mov in perdidas:
            tipo_encontrado = None
            for tipo in ['ROBO', 'MERMA', 'CADUCIDAD', 'DAÑO']:
                if tipo in mov.motivo:
                    tipo_encontrado = tipo.lower()
                    break
            
            if tipo_encontrado:
                perdidas_por_tipo[tipo_encontrado]['cantidad'] += mov.cantidad
                producto = self.bd.obtener_producto(mov.producto_codigo)
                if producto:
                    perdidas_por_tipo[tipo_encontrado]['valor'] += mov.cantidad * producto.precio_compra
        
        return perdidas_por_tipo
    
    def calcular_valor_devoluciones(self):
        devoluciones = self.bd.obtener_movimientos_por_tipo("DEVOLUCION")
        valor_total = 0
        cantidad_total = 0
        
        for mov in devoluciones:
            cantidad_total += mov.cantidad
            producto = self.bd.obtener_producto(mov.producto_codigo)
            if producto:
                valor_total += mov.cantidad * producto.precio_venta
        
        return cantidad_total, valor_total
    
    def productos_mas_vendidos(self, top=5):
        ventas = {}
        movimientos = self.bd.obtener_movimientos_por_tipo("SALIDA")
        
        for mov in movimientos:
            if mov.producto_codigo not in ventas:
                ventas[mov.producto_codigo] = {'nombre': mov.producto_nombre, 'cantidad': 0}
            ventas[mov.producto_codigo]['cantidad'] += mov.cantidad
        
        ordenados = sorted(ventas.items(), key=lambda x: x[1]['cantidad'], reverse=True)
        return [(datos['nombre'], datos['cantidad']) for _, datos in ordenados[:top]]
    
    def valor_total_inventario(self):
        productos = self.bd.obtener_todos_productos()
        return sum(p.precio_compra * p.stock_actual for p in productos)
    
    def reporte_general(self):
        productos = self.bd.obtener_todos_productos()
        categorias = self.bd.obtener_categorias()
        movimientos = self.bd.obtener_movimientos()
        
        return {
            'total_productos': len(productos),
            'categorias': len(categorias),
            'valor_inventario': self.valor_total_inventario(),
            'productos_bajo_stock': len(self.productos_con_stock_bajo()),
            'total_movimientos': len(movimientos)
        }
    
    def cancelar_ultima_operacion(self):
        ultimo_mov = self.bd.eliminar_ultimo_movimiento()
        
        if not ultimo_mov:
            return False, "No hay operaciones para cancelar"
        
        producto = self.bd.obtener_producto(ultimo_mov.producto_codigo)
        if not producto:
            return False, "El producto no existe"
        
        if ultimo_mov.tipo == "ENTRADA":
            if producto.stock_actual < ultimo_mov.cantidad:
                return False, "Stock insuficiente para cancelar"
            producto.stock_actual -= ultimo_mov.cantidad
        elif ultimo_mov.tipo == "SALIDA":
            producto.stock_actual += ultimo_mov.cantidad
        elif ultimo_mov.tipo == "DEVOLUCION":
            if producto.stock_actual < ultimo_mov.cantidad:
                return False, "Stock insuficiente para cancelar"
            producto.stock_actual -= ultimo_mov.cantidad
        elif ultimo_mov.tipo == "PERDIDA":
            producto.stock_actual += ultimo_mov.cantidad
        
        self.bd.actualizar_producto(producto)
        return True, f"Operación cancelada: {ultimo_mov.tipo}"
    
    def ver_ultimas_operaciones(self, cantidad=5):
        return self.obtener_historial(cantidad)


# ============================================================
# INTERFAZ GRÁFICA
# ============================================================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Inventario v2.0")
        self.root.geometry("1200x700")
        
        self.gestor = Gestor()
        
        self.c_primario = "#2c3e50"
        self.c_exito = "#27ae60"
        self.c_peligro = "#e74c3c"
        self.c_acento = "#3498db"
        
        self.crear_menu()
        self.crear_interfaz()
        self.actualizar_tabla()
    
    def crear_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        menu_prod = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Productos", menu=menu_prod)
        menu_prod.add_command(label="Agregar", command=self.ventana_agregar)
        menu_prod.add_command(label="Modificar", command=self.ventana_modificar)
        menu_prod.add_command(label="Eliminar", command=self.eliminar)
        menu_prod.add_command(label="Buscar", command=self.ventana_buscar)
        
        menu_mov = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Movimientos", menu=menu_mov)
        menu_mov.add_command(label="Entrada", command=self.ventana_entrada)
        menu_mov.add_command(label="Salida", command=self.ventana_salida)
        menu_mov.add_command(label="Devolución", command=self.ventana_devolucion)
        menu_mov.add_command(label="Pérdida", command=self.ventana_perdida)
        
        menu_rep = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reportes", menu=menu_rep)
        menu_rep.add_command(label="General", command=self.reporte_general)
        menu_rep.add_command(label="Stock Bajo", command=self.reporte_stock_bajo)
        menu_rep.add_command(label="Más Vendidos", command=self.reporte_vendidos)
        menu_rep.add_command(label="Historial", command=self.reporte_historial)
        menu_rep.add_command(label="Pérdidas", command=self.reporte_perdidas)
        menu_rep.add_command(label="Devoluciones", command=self.reporte_devoluciones)
        
        menu_her = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=menu_her)
        menu_her.add_command(label="Cancelar Operación", command=self.cancelar_operacion)
        menu_her.add_command(label="Actualizar", command=self.actualizar_tabla)
    
    def crear_interfaz(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        titulo = tk.Label(main, text="📦 SISTEMA DE INVENTARIO", 
                         font=("Arial", 20, "bold"), fg=self.c_primario)
        titulo.pack(pady=10)
        
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=10)
        
        botones = [
            ("➕ Agregar", self.ventana_agregar, self.c_exito),
            ("📥 Entrada", self.ventana_entrada, self.c_acento),
            ("📤 Salida", self.ventana_salida, "#e67e22"),
            ("🔍 Buscar", self.ventana_buscar, "#9b59b6"),
            ("📊 Reporte", self.reporte_general, "#16a085")
        ]
        
        for texto, cmd, color in botones:
            btn = tk.Button(btn_frame, text=texto, command=cmd, bg=color, fg='white',
                          font=("Arial", 10, "bold"), padx=15, pady=8, relief=tk.FLAT)
            btn.pack(side=tk.LEFT, padx=5)
        
        table_frame = ttk.Frame(main)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scroll_y = ttk.Scrollbar(table_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(table_frame, 
                                columns=("Código", "Nombre", "P.Compra", "P.Venta", 
                                        "Stock", "Mínimo", "Categoría"),
                                show='headings', yscrollcommand=scroll_y.set, height=20)
        
        scroll_y.config(command=self.tree.yview)
        
        columnas = {
            "Código": 100, "Nombre": 250, "P.Compra": 100,
            "P.Venta": 100, "Stock": 80, "Mínimo": 80, "Categoría": 150
        }
        
        for col, ancho in columnas.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=ancho, anchor=tk.CENTER if col not in ["Nombre", "Categoría"] else tk.W)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.ver_detalles)
    
    def actualizar_stats(self):
        pass  # Ya no se usa, pero se mantiene para evitar errores
    
    def actualizar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        productos = self.gestor.listar_productos()
        
        for p in productos:
            valores = (p.codigo, p.nombre, f"${p.precio_compra:.2f}", 
                      f"${p.precio_venta:.2f}", p.stock_actual, p.stock_minimo, p.categoria)
            
            tag = 'bajo' if p.necesita_reabastecimiento() else ''
            self.tree.insert('', tk.END, values=valores, tags=(tag,))
        
        self.tree.tag_configure('bajo', background='#ffe6e6')
    
    def ventana_agregar(self):
        v = tk.Toplevel(self.root)
        v.title("Agregar Producto")
        v.geometry("500x550")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="➕ AGREGAR PRODUCTO", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        campos = [
            ("Código:", "codigo"),
            ("Nombre:", "nombre"),
            ("Precio Compra:", "precio_compra"),
            ("Precio Venta:", "precio_venta"),
            ("Stock Inicial:", "stock"),
            ("Stock Mínimo:", "minimo"),
            ("Categoría:", "categoria"),
            ("Responsable:", "responsable")
        ]
        
        entries = {}
        
        for label, key in campos:
            f = ttk.Frame(frame)
            f.pack(fill=tk.X, pady=5)
            tk.Label(f, text=label, width=20, anchor='w').pack(side=tk.LEFT)
            entry = ttk.Entry(f, width=30)
            entry.pack(side=tk.LEFT, padx=10)
            entries[key] = entry
        
        def guardar():
            try:
                producto = Producto(
                    codigo=entries['codigo'].get(),
                    nombre=entries['nombre'].get(),
                    precio_compra=float(entries['precio_compra'].get()),
                    precio_venta=float(entries['precio_venta'].get()),
                    stock_actual=int(entries['stock'].get()),
                    stock_minimo=int(entries['minimo'].get()),
                    categoria=entries['categoria'].get()
                )
                
                exito, msg = self.gestor.agregar_producto(producto, entries['responsable'].get())
                
                if exito:
                    messagebox.showinfo("Éxito", msg)
                    self.actualizar_tabla()
                    v.destroy()
                else:
                    messagebox.showerror("Error", msg)
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Guardar", command=guardar, bg=self.c_exito, 
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10, 
                 relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=v.destroy, bg=self.c_peligro,
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
                 relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def ventana_modificar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        codigo = self.tree.item(sel[0])['values'][0]
        producto = self.gestor.bd.obtener_producto(codigo)
        
        if not producto:
            messagebox.showerror("Error", "Producto no encontrado")
            return
        
        v = tk.Toplevel(self.root)
        v.title("Modificar Producto")
        v.geometry("500x450")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"✏️ MODIFICAR: {producto.nombre}", 
                font=("Arial", 14, "bold")).pack(pady=20)
        
        campos = [
            ("Nombre:", "nombre", producto.nombre),
            ("Precio Compra:", "precio_compra", producto.precio_compra),
            ("Precio Venta:", "precio_venta", producto.precio_venta),
            ("Stock Mínimo:", "stock_minimo", producto.stock_minimo),
            ("Categoría:", "categoria", producto.categoria)
        ]
        
        entries = {}
        
        for label, key, valor in campos:
            f = ttk.Frame(frame)
            f.pack(fill=tk.X, pady=5)
            tk.Label(f, text=label, width=20, anchor='w').pack(side=tk.LEFT)
            entry = ttk.Entry(f, width=30)
            entry.insert(0, str(valor))
            entry.pack(side=tk.LEFT, padx=10)
            entries[key] = entry
        
        def guardar():
            try:
                cambios = {}
                if entries['nombre'].get():
                    cambios['nombre'] = entries['nombre'].get()
                if entries['precio_compra'].get():
                    cambios['precio_compra'] = float(entries['precio_compra'].get())
                if entries['precio_venta'].get():
                    cambios['precio_venta'] = float(entries['precio_venta'].get())
                if entries['stock_minimo'].get():
                    cambios['stock_minimo'] = int(entries['stock_minimo'].get())
                if entries['categoria'].get():
                    cambios['categoria'] = entries['categoria'].get()
                
                if cambios:
                    exito, msg = self.gestor.modificar_producto(codigo, **cambios)
                    if exito:
                        messagebox.showinfo("Éxito", msg)
                        self.actualizar_tabla()
                        v.destroy()
                    else:
                        messagebox.showerror("Error", msg)
                else:
                    messagebox.showinfo("Info", "No hay cambios")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Guardar", command=guardar, bg=self.c_exito,
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
                 relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=v.destroy, bg=self.c_peligro,
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
                 relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un producto")
            return
        
        valores = self.tree.item(sel[0])['values']
        codigo = valores[0]
        nombre = valores[1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar {nombre}?"):
            exito, msg = self.gestor.eliminar_producto(codigo)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.actualizar_tabla()
            else:
                messagebox.showerror("Error", msg)
    
    def ventana_buscar(self):
        v = tk.Toplevel(self.root)
        v.title("Buscar Producto")
        v.geometry("700x550")
        
        frame = tk.Frame(v, bg='white', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="🔍 BUSCAR PRODUCTO", font=("Arial", 16, "bold"), 
                bg='white', fg=self.c_primario).pack(pady=(0, 20))
        
        # Frame de búsqueda
        search_frame = tk.Frame(frame, bg='white')
        search_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(search_frame, text="Buscar por:", font=("Arial", 10), bg='white').pack(side=tk.LEFT, padx=5)
        
        criterio_var = tk.StringVar(value="nombre")
        for texto, valor in [("Código", "codigo"), ("Nombre", "nombre"), ("Categoría", "categoria")]:
            tk.Radiobutton(search_frame, text=texto, variable=criterio_var,
                          value=valor, bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=8)
        
        # Entry de búsqueda
        input_frame = tk.Frame(frame, bg='white')
        input_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(input_frame, text="Texto a buscar:", font=("Arial", 10), bg='white').pack(side=tk.LEFT, padx=5)
        entry = tk.Entry(input_frame, width=35, font=("Arial", 11), relief=tk.SOLID, borderwidth=1)
        entry.pack(side=tk.LEFT, padx=10)
        
        # Área de resultados
        result_frame = tk.Frame(frame, bg='white')
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(result_frame, text="Resultados:", font=("Arial", 10, "bold"), 
                bg='white').pack(anchor='w', pady=(5, 5))
        
        result_text = scrolledtext.ScrolledText(result_frame, height=15, font=("Courier", 10),
                                                relief=tk.SOLID, borderwidth=1)
        result_text.pack(fill=tk.BOTH, expand=True)
        
        result_text.insert(tk.END, "Ingrese un criterio de búsqueda y presione 'Buscar'\n")
        result_text.insert(tk.END, "O presione 'Ver Todos' para listar todos los productos...")
        result_text.config(state=tk.DISABLED)
        
        # Función para mostrar productos
        def mostrar_productos(productos, titulo):
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            
            if productos:
                result_text.insert(tk.END, f"✓ {titulo}: {len(productos)} producto(s)\n\n")
                for i, p in enumerate(productos, 1):
                    result_text.insert(tk.END, f"{'='*65}\n")
                    result_text.insert(tk.END, f"#{i}\n")
                    result_text.insert(tk.END, f"Código:         {p.codigo}\n")
                    result_text.insert(tk.END, f"Nombre:         {p.nombre}\n")
                    result_text.insert(tk.END, f"Categoría:      {p.categoria}\n")
                    result_text.insert(tk.END, f"Precio Compra:  ${p.precio_compra:.2f}\n")
                    result_text.insert(tk.END, f"Precio Venta:   ${p.precio_venta:.2f}\n")
                    result_text.insert(tk.END, f"Stock Actual:   {p.stock_actual} unidades\n")
                    result_text.insert(tk.END, f"Stock Mínimo:   {p.stock_minimo} unidades\n")
                    
                    if p.necesita_reabastecimiento():
                        result_text.insert(tk.END, f"Estado:         ⚠️ STOCK BAJO\n")
                    else:
                        result_text.insert(tk.END, f"Estado:         ✓ Stock OK\n")
                    
                    result_text.insert(tk.END, f"{'='*65}\n\n")
            else:
                result_text.insert(tk.END, "❌ No se encontraron productos.\n\n")
            
            result_text.config(state=tk.DISABLED)
        
        # Función buscar
        def buscar():
            criterio = criterio_var.get()
            valor = entry.get().strip()
            
            if not valor:
                messagebox.showwarning("Campo vacío", "Ingrese un valor para buscar")
                entry.focus()
                return
            
            resultados = self.gestor.buscar_producto(criterio, valor)
            mostrar_productos(resultados, f"Resultados de búsqueda por {criterio}")
        
        # Función ver todos
        def ver_todos():
            todos = self.gestor.listar_productos()
            mostrar_productos(todos, "Todos los productos en inventario")
        
        # Botones
        btn_buscar = tk.Button(input_frame, text="🔍 Buscar", command=buscar,
                              bg=self.c_acento, fg='white', font=("Arial", 11, "bold"),
                              relief=tk.FLAT, padx=25, pady=8, cursor='hand2')
        btn_buscar.pack(side=tk.LEFT, padx=5)
        
        btn_ver_todos = tk.Button(input_frame, text="📋 Ver Todos", command=ver_todos,
                                 bg='#16a085', fg='white', font=("Arial", 11, "bold"),
                                 relief=tk.FLAT, padx=25, pady=8, cursor='hand2')
        btn_ver_todos.pack(side=tk.LEFT, padx=5)
        
        # Permitir buscar con Enter
        entry.bind('<Return>', lambda e: buscar())
    
    def ventana_entrada(self):
        self.ventana_movimiento("ENTRADA", "📥 Entrada")
    
    def ventana_salida(self):
        self.ventana_movimiento("SALIDA", "📤 Salida")
    
    def ventana_movimiento(self, tipo, titulo):
        v = tk.Toplevel(self.root)
        v.title(titulo)
        v.geometry("500x500")
        v.resizable(False, False)
        
        frame = tk.Frame(v, bg='white', padx=30, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        color_titulo = self.c_exito if tipo == "ENTRADA" else "#e67e22"
        tk.Label(frame, text=titulo, font=("Arial", 16, "bold"), 
                bg='white', fg=color_titulo).pack(pady=(0, 20))
        
        # Código
        tk.Label(frame, text="Código del producto:", font=("Arial", 10), 
                bg='white', anchor='w').pack(fill=tk.X, pady=(10, 2))
        entry_codigo = tk.Entry(frame, width=40, font=("Arial", 11), 
                               relief=tk.SOLID, borderwidth=1)
        entry_codigo.pack(pady=(0, 5))
        
        # Frame de información
        info_frame = tk.Frame(frame, bg='#f8f9fa', relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.X, pady=10, ipady=8)
        
        info_label = tk.Label(info_frame, text="Ingrese el código y presione 'Buscar'", 
                             font=("Arial", 9), bg='#f8f9fa', fg='gray')
        info_label.pack()
        
        # Botón buscar
        def buscar():
            codigo = entry_codigo.get().strip()
            if not codigo:
                info_label.config(text="⚠️ Ingrese un código primero", fg='orange')
                return
            
            producto = self.gestor.bd.obtener_producto(codigo)
            if producto:
                info_label.config(
                    text=f"✓ {producto.nombre}\nStock disponible: {producto.stock_actual} unidades",
                    fg='#27ae60', font=("Arial", 10, "bold")
                )
            else:
                info_label.config(text="❌ Producto NO encontrado", fg='red', font=("Arial", 10, "bold"))
        
        btn_buscar = tk.Button(frame, text="🔍 Buscar Producto", command=buscar,
                              bg='#3498db', fg='white', font=("Arial", 10, "bold"),
                              relief=tk.FLAT, padx=20, pady=8, cursor='hand2',
                              activebackground='#2980b9')
        btn_buscar.pack(pady=5)
        
        # Separador
        tk.Frame(frame, height=2, bg='#ddd').pack(fill=tk.X, pady=15)
        
        # Cantidad
        tk.Label(frame, text="Cantidad:", font=("Arial", 10), 
                bg='white', anchor='w').pack(fill=tk.X, pady=(5, 2))
        entry_cantidad = tk.Entry(frame, width=40, font=("Arial", 11),
                                 relief=tk.SOLID, borderwidth=1)
        entry_cantidad.pack(pady=(0, 10))
        
        # Responsable
        tk.Label(frame, text="Responsable:", font=("Arial", 10),
                bg='white', anchor='w').pack(fill=tk.X, pady=(5, 2))
        entry_resp = tk.Entry(frame, width=40, font=("Arial", 11),
                             relief=tk.SOLID, borderwidth=1)
        entry_resp.pack(pady=(0, 20))
        
        # Función guardar
        def guardar():
            try:
                codigo = entry_codigo.get().strip()
                cantidad_str = entry_cantidad.get().strip()
                resp = entry_resp.get().strip()
                
                # Validaciones
                if not codigo:
                    messagebox.showwarning("Campo vacío", "Ingrese el código del producto")
                    entry_codigo.focus()
                    return
                
                if not cantidad_str:
                    messagebox.showwarning("Campo vacío", "Ingrese la cantidad")
                    entry_cantidad.focus()
                    return
                
                if not resp:
                    messagebox.showwarning("Campo vacío", "Ingrese el responsable")
                    entry_resp.focus()
                    return
                
                # Convertir cantidad
                try:
                    cantidad = int(cantidad_str)
                    if cantidad <= 0:
                        messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                        return
                except ValueError:
                    messagebox.showerror("Error", "La cantidad debe ser un número entero")
                    return
                
                # Registrar operación
                if tipo == "ENTRADA":
                    exito, msg = self.gestor.registrar_entrada(codigo, cantidad, resp)
                else:
                    exito, msg = self.gestor.registrar_salida(codigo, cantidad, resp)
                
                if exito:
                    messagebox.showinfo("✓ Operación exitosa", msg)
                    self.actualizar_tabla()
                    v.destroy()
                else:
                    messagebox.showerror("Error", msg)
                    
            except Exception as e:
                messagebox.showerror("Error inesperado", str(e))
        
        # Frame de botones
        btn_frame = tk.Frame(frame, bg='white')
        btn_frame.pack(pady=(10, 0))
        
        # Botón guardar
        color_guardar = '#27ae60' if tipo == "ENTRADA" else '#e67e22'
        texto_guardar = "💾 Registrar Entrada" if tipo == "ENTRADA" else "💾 Registrar Salida"
        
        btn_guardar = tk.Button(btn_frame, text=texto_guardar, command=guardar,
                               bg=color_guardar, fg='white', font=("Arial", 12, "bold"),
                               relief=tk.FLAT, padx=25, pady=12, cursor='hand2',
                               activebackground='#229954' if tipo == "ENTRADA" else '#d35400')
        btn_guardar.pack(side=tk.LEFT, padx=5)
        
        # Botón cancelar
        btn_cancelar = tk.Button(btn_frame, text="❌ Cancelar", command=v.destroy,
                                bg='#95a5a6', fg='white', font=("Arial", 12, "bold"),
                                relief=tk.FLAT, padx=25, pady=12, cursor='hand2',
                                activebackground='#7f8c8d')
        btn_cancelar.pack(side=tk.LEFT, padx=5)
    
    def ventana_devolucion(self):
        v = tk.Toplevel(self.root)
        v.title("Devolución")
        v.geometry("450x500")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="🔄 DEVOLUCIÓN", font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Label(frame, text="Código del producto:").pack(anchor='w')
        entry_codigo = ttk.Entry(frame, width=40)
        entry_codigo.pack(pady=5)
        
        tk.Label(frame, text="Cantidad a devolver:").pack(anchor='w', pady=(10, 0))
        entry_cantidad = ttk.Entry(frame, width=40)
        entry_cantidad.pack(pady=5)
        
        tk.Label(frame, text="Motivo de la devolución:").pack(anchor='w', pady=(10, 0))
        entry_motivo = ttk.Entry(frame, width=40)
        entry_motivo.pack(pady=5)
        
        tk.Label(frame, text="Sugerencias:", font=("Arial", 9, "italic"), fg='gray').pack(anchor='w', pady=(5,0))
        tk.Label(frame, text="• Producto defectuoso\n• Cliente insatisfecho\n• Error en venta", 
                font=("Arial", 8), fg='gray', justify=tk.LEFT).pack(anchor='w', padx=10)
        
        tk.Label(frame, text="Responsable:").pack(anchor='w', pady=(10, 0))
        entry_resp = ttk.Entry(frame, width=40)
        entry_resp.pack(pady=5)
        
        def guardar():
            try:
                codigo = entry_codigo.get().strip()
                cantidad = entry_cantidad.get().strip()
                motivo = entry_motivo.get().strip()
                resp = entry_resp.get().strip()
                
                if not codigo or not cantidad or not motivo or not resp:
                    messagebox.showwarning("Advertencia", "Complete todos los campos")
                    return
                
                exito, msg = self.gestor.registrar_devolucion(
                    codigo, int(cantidad), motivo, resp
                )
                
                if exito:
                    messagebox.showinfo("Éxito", msg)
                    self.actualizar_tabla()
                    v.destroy()
                else:
                    messagebox.showerror("Error", msg)
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Registrar Devolución", command=guardar, bg=self.c_exito,
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=v.destroy, bg=self.c_peligro,
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def ventana_perdida(self):
        v = tk.Toplevel(self.root)
        v.title("Pérdida")
        v.geometry("450x550")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="⚠️ REGISTRAR PÉRDIDA", font=("Arial", 14, "bold"), 
                fg=self.c_peligro).pack(pady=20)
        
        tk.Label(frame, text="Código del producto:").pack(anchor='w')
        entry_codigo = ttk.Entry(frame, width=40)
        entry_codigo.pack(pady=5)
        
        tk.Label(frame, text="Tipo de pérdida:").pack(anchor='w', pady=(10, 0))
        tipo_var = tk.StringVar(value="robo")
        
        tipos_frame = ttk.Frame(frame)
        tipos_frame.pack(anchor='w', pady=5)
        
        for texto, valor in [("Robo", "robo"), ("Merma", "merma"), 
                             ("Caducidad", "caducidad"), ("Daño", "daño")]:
            tk.Radiobutton(tipos_frame, text=texto, variable=tipo_var,
                          value=valor, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        
        tk.Label(frame, text="Cantidad perdida:").pack(anchor='w', pady=(10, 0))
        entry_cantidad = ttk.Entry(frame, width=40)
        entry_cantidad.pack(pady=5)
        
        tk.Label(frame, text="Descripción detallada:").pack(anchor='w', pady=(10, 0))
        entry_motivo = ttk.Entry(frame, width=40)
        entry_motivo.pack(pady=5)
        
        tk.Label(frame, text="Responsable del registro:").pack(anchor='w', pady=(10, 0))
        entry_resp = ttk.Entry(frame, width=40)
        entry_resp.pack(pady=5)
        
        def guardar():
            try:
                codigo = entry_codigo.get().strip()
                cantidad = entry_cantidad.get().strip()
                tipo = tipo_var.get()
                motivo = entry_motivo.get().strip()
                resp = entry_resp.get().strip()
                
                if not codigo or not cantidad or not motivo or not resp:
                    messagebox.showwarning("Advertencia", "Complete todos los campos")
                    return
                
                exito, msg = self.gestor.registrar_perdida(
                    codigo, int(cantidad), tipo, motivo, resp
                )
                
                if exito:
                    messagebox.showinfo("Éxito", msg)
                    self.actualizar_tabla()
                    v.destroy()
                else:
                    messagebox.showerror("Error", msg)
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Registrar Pérdida", command=guardar, bg=self.c_peligro,
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=v.destroy, bg='gray',
                 fg='white', font=("Arial", 11, "bold"), padx=20, pady=10,
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def reporte_general(self):
        v = tk.Toplevel(self.root)
        v.title("Reporte General")
        v.geometry("500x350")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="📊 REPORTE GENERAL", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        reporte = self.gestor.reporte_general()
        
        info = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        info.pack(fill=tk.BOTH, expand=True)
        
        datos = [
            ("📦 Total Productos:", reporte['total_productos']),
            ("🏷️ Categorías:", reporte['categorias']),
            ("💰 Valor Inventario:", f"${reporte['valor_inventario']:.2f}"),
            ("⚠️ Stock Bajo:", reporte['productos_bajo_stock']),
            ("📝 Movimientos:", reporte['total_movimientos'])
        ]
        
        for label, valor in datos:
            f = tk.Frame(info)
            f.pack(fill=tk.X, padx=20, pady=10)
            tk.Label(f, text=label, font=("Arial", 11), anchor='w').pack(side=tk.LEFT)
            tk.Label(f, text=str(valor), font=("Arial", 11, "bold"),
                    fg=self.c_acento, anchor='e').pack(side=tk.RIGHT)
    
    def reporte_stock_bajo(self):
        productos = self.gestor.productos_con_stock_bajo()
        
        if not productos:
            messagebox.showinfo("Stock Bajo", "Stock suficiente")
            return
        
        v = tk.Toplevel(self.root)
        v.title("Stock Bajo")
        v.geometry("800x400")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"⚠️ STOCK BAJO ({len(productos)})", 
                font=("Arial", 14, "bold"), fg=self.c_peligro).pack(pady=20)
        
        tree = ttk.Treeview(frame, columns=("Código", "Nombre", "Stock", "Mínimo"),
                           show='headings', height=12)
        
        for col in ["Código", "Nombre", "Stock", "Mínimo"]:
            tree.heading(col, text=col)
        
        for p in productos:
            tree.insert('', tk.END, values=(p.codigo, p.nombre, p.stock_actual, p.stock_minimo))
        
        tree.pack(fill=tk.BOTH, expand=True)
    
    def reporte_vendidos(self):
        v = tk.Toplevel(self.root)
        v.title("Más Vendidos")
        v.geometry("600x400")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="🏆 MÁS VENDIDOS", font=("Arial", 14, "bold")).pack(pady=20)
        
        result_text = scrolledtext.ScrolledText(frame, height=15, font=("Courier", 10))
        result_text.pack(fill=tk.BOTH, expand=True)
        
        resultado = self.gestor.productos_mas_vendidos(5)
        
        if resultado:
            result_text.insert(tk.END, f"{'#':<5} {'Producto':<40} {'Vendidos':<10}\n")
            result_text.insert(tk.END, "="*60 + "\n")
            
            for i, (nombre, cantidad) in enumerate(resultado, 1):
                result_text.insert(tk.END, f"{i:<5} {nombre:<40} {cantidad:<10}\n")
        else:
            result_text.insert(tk.END, "No hay ventas")
    
    def reporte_historial(self):
        v = tk.Toplevel(self.root)
        v.title("Historial")
        v.geometry("1000x600")
        
        frame = ttk.Frame(v, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="📝 HISTORIAL", font=("Arial", 14, "bold")).pack(pady=20)
        
        tree = ttk.Treeview(frame,
                           columns=("Fecha", "Tipo", "Producto", "Cantidad", "Responsable"),
                           show='headings', height=20)
        
        for col in ["Fecha", "Tipo", "Producto", "Cantidad", "Responsable"]:
            tree.heading(col, text=col)
        
        movimientos = self.gestor.obtener_historial(50)
        
        for m in movimientos:
            fecha_str = m.fecha.strftime("%Y-%m-%d %H:%M")
            tree.insert('', tk.END, values=(fecha_str, m.tipo, m.producto_nombre,
                                           m.cantidad, m.responsable))
        
        tree.pack(fill=tk.BOTH, expand=True)
    
    def reporte_perdidas(self):
        v = tk.Toplevel(self.root)
        v.title("Reporte de Pérdidas")
        v.geometry("900x650")
        
        frame = tk.Frame(v, bg='white', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="💸 REPORTE DE PÉRDIDAS", 
                font=("Arial", 16, "bold"), bg='white', fg=self.c_peligro).pack(pady=(0, 20))
        
        # Filtros
        filtro_frame = tk.Frame(frame, bg='white')
        filtro_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(filtro_frame, text="Filtrar por tipo:", font=("Arial", 10), bg='white').pack(side=tk.LEFT, padx=5)
        
        tipo_var = tk.StringVar(value="todas")
        for texto, valor in [("Todas", "todas"), ("Robo", "robo"), ("Merma", "merma"), 
                             ("Caducidad", "caducidad"), ("Daño", "daño")]:
            tk.Radiobutton(filtro_frame, text=texto, variable=tipo_var, value=valor, 
                          bg='white', font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Resumen de pérdidas
        resumen_frame = tk.Frame(frame, bg='#ffe6e6', relief=tk.SOLID, borderwidth=1)
        resumen_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(resumen_frame, text="RESUMEN FINANCIERO", font=("Arial", 11, "bold"), 
                bg='#ffe6e6').pack(pady=10)
        
        tree_resumen = ttk.Treeview(resumen_frame, columns=("Tipo", "Cantidad", "Valor"),
                                   show='headings', height=5)
        
        tree_resumen.heading("Tipo", text="Tipo de Pérdida")
        tree_resumen.heading("Cantidad", text="Unidades Perdidas")
        tree_resumen.heading("Valor", text="Valor ($)")
        
        tree_resumen.column("Tipo", width=200, anchor=tk.CENTER)
        tree_resumen.column("Cantidad", width=150, anchor=tk.CENTER)
        tree_resumen.column("Valor", width=150, anchor=tk.CENTER)
        
        def actualizar_resumen():
            for item in tree_resumen.get_children():
                tree_resumen.delete(item)
            
            perdidas_totales = self.gestor.calcular_perdidas_totales()
            
            total_cant = 0
            total_val = 0
            
            for tipo, datos in perdidas_totales.items():
                if datos['cantidad'] > 0:
                    tree_resumen.insert('', tk.END, 
                                       values=(tipo.capitalize(), datos['cantidad'], f"${datos['valor']:.2f}"))
                    total_cant += datos['cantidad']
                    total_val += datos['valor']
            
            if total_cant > 0:
                tree_resumen.insert('', tk.END, values=("━━━ TOTAL ━━━", total_cant, f"${total_val:.2f}"),
                                   tags=('total',))
                tree_resumen.tag_configure('total', background='#ffcccc', font=('Arial', 10, 'bold'))
        
        tree_resumen.pack(pady=10, padx=10)
        actualizar_resumen()
        
        # Detalle de pérdidas
        tk.Label(frame, text="DETALLE DE PÉRDIDAS", font=("Arial", 11, "bold"), 
                bg='white').pack(pady=(20, 10))
        
        detalle_frame = tk.Frame(frame, bg='white')
        detalle_frame.pack(fill=tk.BOTH, expand=True)
        
        scroll_y = ttk.Scrollbar(detalle_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_detalle = ttk.Treeview(detalle_frame,
                                    columns=("Fecha", "Producto", "Cantidad", "Tipo", "Motivo", "Responsable"),
                                    show='headings', yscrollcommand=scroll_y.set, height=12)
        
        scroll_y.config(command=tree_detalle.yview)
        
        tree_detalle.heading("Fecha", text="Fecha")
        tree_detalle.heading("Producto", text="Producto")
        tree_detalle.heading("Cantidad", text="Cant.")
        tree_detalle.heading("Tipo", text="Tipo")
        tree_detalle.heading("Motivo", text="Motivo")
        tree_detalle.heading("Responsable", text="Responsable")
        
        tree_detalle.column("Fecha", width=130, anchor=tk.CENTER)
        tree_detalle.column("Producto", width=180)
        tree_detalle.column("Cantidad", width=70, anchor=tk.CENTER)
        tree_detalle.column("Tipo", width=90, anchor=tk.CENTER)
        tree_detalle.column("Motivo", width=200)
        tree_detalle.column("Responsable", width=130)
        
        def actualizar_detalle():
            for item in tree_detalle.get_children():
                tree_detalle.delete(item)
            
            tipo_filtro = None if tipo_var.get() == "todas" else tipo_var.get()
            perdidas = self.gestor.obtener_perdidas(tipo_filtro)
            
            if perdidas:
                for p in perdidas[:50]:  # Últimas 50
                    fecha_str = p.fecha.strftime("%Y-%m-%d %H:%M")
                    
                    # Extraer tipo del motivo
                    tipo_display = "Otro"
                    for tipo in ['ROBO', 'MERMA', 'CADUCIDAD', 'DAÑO']:
                        if tipo in p.motivo:
                            tipo_display = tipo.capitalize()
                            break
                    
                    motivo_limpio = p.motivo.replace(f"[{tipo_display.upper()}] ", "")
                    
                    tree_detalle.insert('', tk.END, 
                                       values=(fecha_str, p.producto_nombre, p.cantidad, 
                                              tipo_display, motivo_limpio, p.responsable))
            
            info_text = f"Total de pérdidas: {len(perdidas)}"
            if tipo_filtro:
                info_text += f" (filtradas por {tipo_filtro})"
            tk.Label(frame, text=info_text, font=("Arial", 9, "italic"), bg='white', fg='gray').pack()
        
        tree_detalle.pack(fill=tk.BOTH, expand=True)
        
        btn_actualizar = tk.Button(filtro_frame, text="🔄 Aplicar Filtro", command=actualizar_detalle,
                                   bg=self.c_acento, fg='white', font=("Arial", 9, "bold"),
                                   relief=tk.FLAT, padx=15, pady=5, cursor='hand2')
        btn_actualizar.pack(side=tk.LEFT, padx=10)
        
        actualizar_detalle()
    
    def reporte_devoluciones(self):
        v = tk.Toplevel(self.root)
        v.title("Historial de Devoluciones")
        v.geometry("1000x600")
        
        frame = tk.Frame(v, bg='white', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="🔄 HISTORIAL DE DEVOLUCIONES", 
                font=("Arial", 16, "bold"), bg='white', fg=self.c_acento).pack(pady=(0, 20))
        
        devoluciones = self.gestor.obtener_devoluciones()
        
        if not devoluciones:
            tk.Label(frame, text="No hay devoluciones registradas", 
                    font=("Arial", 14), bg='white', fg='gray').pack(pady=100)
            return
        
        # Estadísticas
        cantidad_total, valor_total = self.gestor.calcular_valor_devoluciones()
        
        stats_frame = tk.Frame(frame, bg='#e3f2fd', relief=tk.SOLID, borderwidth=1)
        stats_frame.pack(fill=tk.X, pady=10)
        
        stats_info = f"📊 Total de devoluciones: {len(devoluciones)}  |  " \
                    f"📦 Unidades devueltas: {cantidad_total}  |  " \
                    f"💰 Valor estimado: ${valor_total:.2f}"
        
        tk.Label(stats_frame, text=stats_info, font=("Arial", 11, "bold"), 
                bg='#e3f2fd', fg='#1565c0').pack(pady=12)
        
        # Tabla de devoluciones
        table_frame = tk.Frame(frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        scroll_y = ttk.Scrollbar(table_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(table_frame,
                           columns=("Fecha", "Producto", "Cantidad", "Motivo", "Responsable"),
                           show='headings', yscrollcommand=scroll_y.set, height=18)
        
        scroll_y.config(command=tree.yview)
        
        tree.heading("Fecha", text="Fecha y Hora")
        tree.heading("Producto", text="Producto")
        tree.heading("Cantidad", text="Cantidad")
        tree.heading("Motivo", text="Motivo de Devolución")
        tree.heading("Responsable", text="Responsable")
        
        tree.column("Fecha", width=150, anchor=tk.CENTER)
        tree.column("Producto", width=220)
        tree.column("Cantidad", width=80, anchor=tk.CENTER)
        tree.column("Motivo", width=280)
        tree.column("Responsable", width=150)
        
        for d in devoluciones:
            fecha_str = d.fecha.strftime("%Y-%m-%d %H:%M:%S")
            tree.insert('', tk.END, 
                       values=(fecha_str, d.producto_nombre, d.cantidad, d.motivo, d.responsable))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Botón exportar (placeholder)
        btn_frame = tk.Frame(frame, bg='white')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🔄 Actualizar", 
                 command=lambda: [v.destroy(), self.reporte_devoluciones()],
                 bg=self.c_acento, fg='white', font=("Arial", 10, "bold"),
                 relief=tk.FLAT, padx=20, pady=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def cancelar_operacion(self):
        if messagebox.askyesno("Confirmar", "¿Cancelar última operación?"):
            exito, msg = self.gestor.cancelar_ultima_operacion()
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.actualizar_tabla()
            else:
                messagebox.showerror("Error", msg)
    
    def ver_detalles(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        
        codigo = self.tree.item(sel[0])['values'][0]
        producto = self.gestor.bd.obtener_producto(codigo)
        
        if producto:
            info = f"""
Código:    {producto.codigo}
Nombre:    {producto.nombre}
Categoría: {producto.categoria}

P.Compra:  ${producto.precio_compra:.2f}
P.Venta:   ${producto.precio_venta:.2f}

Stock:     {producto.stock_actual}
Mínimo:    {producto.stock_minimo}
            """
            messagebox.showinfo("Detalles", info)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()