import sqlite3
import os

def rename_column_in_sqlite(db_path, table_name, old_column_name, new_column_name):
    """
    Connette a un database SQLite e rinomina una colonna in una tabella specificata.

    Args:
        db_path (str): Il percorso completo al file del database SQLite (es. 'project.db').
        table_name (str): Il nome della tabella in cui rinominare la colonna (es. 'quiz_plugin_question').
        old_column_name (str): Il nome attuale della colonna (es. 'texto').
        new_column_name (str): Il nuovo nome desiderato per la colonna (es. 'text').
    """
    if not os.path.exists(db_path):
        print(f"Errore: Il database '{db_path}' non è stato trovato.")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verifica se la colonna vecchia esiste
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_exists = False
        for col in columns:
            if col[1] == old_column_name: # col[1] è il nome della colonna
                column_exists = True
                break
        
        if not column_exists:
            print(f"Errore: La colonna '{old_column_name}' non esiste nella tabella '{table_name}'.")
            return

        # Costruisci la query SQL per rinominare la colonna
        sql_query = f"ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name};"
        
        print(f"Esecuzione query SQL: {sql_query}")
        cursor.execute(sql_query)
        conn.commit()
        print(f"Colonna '{old_column_name}' rinominata con successo in '{new_column_name}' nella tabella '{table_name}'.")

    except sqlite3.Error as e:
        print(f"Si è verificato un errore del database: {e}")
        if conn:
            conn.rollback() # Annulla le modifiche in caso di errore
    except Exception as e:
        print(f"Si è verificato un errore inaspettato: {e}")
    finally:
        if conn:
            conn.close()
            print("Connessione al database chiusa.")

if __name__ == "__main__":
    # Definisci il percorso al tuo file del database
    DATABASE_FILE = 'project.db' 
    OLD_COLUMN = 'texto'
    NEW_COLUMN = 'text'


    # Rinomina la colonna per la tabella Answer
    TABLE_NAME_ANSWER = 'quiz_plugin_answer' # Nome della tabella Answer nel database
    print(f"\nTentativo di rinominare la colonna '{OLD_COLUMN}' in '{NEW_COLUMN}' nella tabella '{TABLE_NAME_ANSWER}' del database '{DATABASE_FILE}'.")
    rename_column_in_sqlite(DATABASE_FILE, TABLE_NAME_ANSWER, OLD_COLUMN, NEW_COLUMN)
