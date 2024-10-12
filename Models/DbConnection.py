#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import os
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, \
    DateTime, Numeric, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv(override=True)


class DbConnection:
    has_debug = os.getenv("DEBUG") == "True"

    # Datos de conexión con la DB desde .env
    DB_CONNECTION = os.getenv("DB_CONNECTION")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_DATABASE = os.getenv("DB_DATABASE")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # Conexión a la base de datos
    if DB_CONNECTION == 'sqlite':
        str_conn = DB_CONNECTION + ':///' + DB_DATABASE
    else:
        str_conn = f"{DB_CONNECTION}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}"

        if DB_PORT and int(DB_PORT) > 0:
            str_conn += f":{DB_PORT}"
        str_conn += f"/{DB_DATABASE}"

    engine = create_engine(str_conn)
    meta = MetaData()
    connection = engine.connect()

    # Sesión para acciones por lotes
    Session = sessionmaker(bind=engine)
    session = Session()

    tables = { }

    def table_set_new (self, tablename, parameters):
        """
        Almacena una nueva tabla en el array de tablas.
        :param tablename: Nombre de la tabla.
        :param parameters: Parámetros para cada columna.
        """
        columns = []

        # Seteo la columna **id**
        columns.append(
            Column('id', Integer, primary_key=True, autoincrement=True))

        # Seteo el resto de columnas.
        for column_name, attributes in parameters.items():
            data_type = attributes['type']
            data_params = attributes.get('params', { })
            other_data = attributes.get('others', { })

            # Creo el campo según el tipo de dato.
            if data_type == 'Numeric':
                type_column = Numeric(**data_params)
            elif data_type == 'DateTime':
                type_column = DateTime
            elif data_type == 'Integer':
                type_column = Integer
            elif data_type == 'String':
                type_column = String(**data_params)
            else:
                type_column = String  # Fallback por si no hay tipo definido.

            # Aseguramos que other_data es un diccionario
            other_data = other_data if other_data else { }

            columns.append(Column(column_name, type_column, **other_data))

        # Creo la tabla con las columnas antes seteadas.
        self.tables[tablename] = Table(
            tablename,
            self.meta,
            *columns,
            extend_existing=True
            # Esta línea permite redefinir la tabla si ya existe.
        )

        self.meta.create_all(self.engine)

        if self.has_debug:
            self.meta.reflect(bind=self.engine)
            print('Tablas en la DB: ', list(self.meta.tables.keys()))

    def table_get_data (self, tablename):
        """
        Obtiene los datos de una tabla previamente seteada.
        :param tablename: Nombre de la tabla desde la que obtener datos.
        """
        table = self.tables[tablename]

        # Ejecuto la consulta para traer las tuplas de la tabla completa
        with self.engine.connect() as con:
            result = con.execute(select(table))
            return result.fetchall()

    def table_get_data_last (self, tablename, limit):
        """
        Obtiene los datos de una tabla previamente seteada limitando resultados.
        :param tablename: Nombre de la tabla desde la que obtener datos.
        :param limit: Límite de datos a extraer de la db
        """
        table = self.tables[tablename]

        if self.has_debug:
            print('----------- table_get_data_last ------------')

        # Ejecuto la consulta para traer las tuplas de la tabla limitada
        with self.engine.connect() as con:
            result = con.execute(
                select(table).order_by(text('created_at DESC')).limit(limit))
            return result.fetchall()

    def table_save_data (self, tablename, params):
        """
        Almacena datos recibidos en la tabla recibida.
        :param tablename: Nombre de la tabla en la que guardar.
        :param params: Diccionario con los parámetros del sensor.
        """
        table = self.tables[tablename]

        # Inserto Datos
        try:
            if self.has_debug:
                print('Intentando guardar en la DB: ', params)

            stmt = table.insert().values(params).returning(table.c.id)
            with self.engine.connect() as con:
                result = con.execute(stmt)
                server_created_at = result.first()[0]
                con.commit()
                return server_created_at

        except SQLAlchemyError as e:
            if self.has_debug:
                print('Ha ocurrido un problema al insertar datos', e,
                      type(e).__name__)
            self.session.rollback()
            return None

    def table_truncate (self, tablename):
        """
        Vacia completamente la tabla recibida.
        :param tablename: Nombre de la tabla.
        """
        with self.engine.connect() as con:
            con.execute(self.tables[tablename].delete())

    def table_drop_last_elements (self, tablename, limit):
        """
        Elimina los últimos elementos en la cantidad recibida, de una
        tabla recibida.
        :param tablename: Nombre de la tabla sobre la que actuar.
        :param limit: Límite, cantidad de entradas a borrar.
        :return:
        """
        table = self.tables.get(tablename)

        if table is None:
            if self.has_debug:
                print(f"La tabla {tablename} no existe.")
            return

        # Obtengo los últimos elementos para eliminarlos posteriormente.
        last_data = self.table_get_data_last(tablename, limit)

        # Comprueba si se encontraron datos.
        if len(last_data) == 0:
            if self.has_debug:
                print(
                    f"No se encontraron datos en la tabla {tablename} para eliminar.")
            return

        # Almaceno los ids de todos los resultados.
        ids = [data.id for data in last_data]

        query = table.delete().where(table.c.id.in_(ids))

        try:
            # Utiliza la session creada en lugar de intentar usar Session sin una instancia.
            self.session.execute(query)
            self.session.commit()
        except SQLAlchemyError as e:
            if self.has_debug:
                print(f"Error al eliminar elementos en {tablename}: {str(e)}")
            self.session.rollback()

    def get_all_data (self):
        """
        Obtiene todos los datos de la base de datos para todas las
        tablas y los devuelve organizados.
        """
        pass

    def truncate_all_table_data (self):
        """
        Limpia todas las tablas establecidas.
        """
        pass

    def truncate_db (self):
        """
        Limpia la Base de datos completamente para comenzar a recopilar
        información desde una base de datos saneada/limpia.
        """
        with self.engine.connect() as con:
            trans = con.begin()
            con.execute('SET FOREIGN_KEY_CHECKS = 0;')
            for table in self.meta.sorted_tables:
                con.execute(table.delete())
            con.execute('SET FOREIGN_KEY_CHECKS = 1;')
            trans.commit()

    def close_connection (self):
        if self.has_debug:
            print('Cerrando conexión con la Base de Datos')

        self.connection.close()
        self.session.close()
