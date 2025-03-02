import pandas as pd
import os

def load_contacts_file(file_uploaded):
    """
    Charge un fichier contacts au format CSV ou Excel
    et retourne un DataFrame.
    """
    file_name = file_uploaded.name.lower()
    if file_name.endswith('.csv'):
        df = pd.read_csv(file_uploaded)
    elif file_name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_uploaded)
    else:
        raise ValueError("Format de fichier non supporté. Veuillez utiliser CSV ou Excel.")
    print("Log (utils): Contacts chargé avec colonnes:", df.columns.tolist())
    return df

def save_uploaded_places(places_files, upload_folder):
    """
    Sauvegarde les fichiers uploadés dans un dossier local et retourne la liste des chemins.
    """
    saved_paths = []
    for f in places_files:
        file_path = os.path.join(upload_folder, f.name)
        with open(file_path, "wb") as out_file:
            out_file.write(f.getbuffer())
        saved_paths.append(file_path)
        print(f"Log (utils): Fichier sauvegardé : {file_path}")
    return saved_paths

def create_distribution_mapping(contacts_df, places_paths):
    """
    Associe chaque contact à un fichier de place en utilisant l'ordre d'apparition.
    Si le nombre de places dépasse celui des contacts, ajoute une ligne avec "Non attribué".
    Pour le récapitulatif, seule la partie nom de fichier est conservée.
    """
    mapping = []
    nb_contacts = len(contacts_df)
    nb_places = len(places_paths)
    print(f"Log (utils): Nombre de contacts: {nb_contacts}, Nombre de places: {nb_places}")

    max_rows = max(nb_contacts, nb_places)
    for idx in range(max_rows):
        email_addr = contacts_df.iloc[idx]["email"] if idx < nb_contacts else "Non attribué"
        if idx < nb_places:
            file_name = os.path.basename(places_paths[idx])
        else:
            file_name = "Non attribué"
        mapping.append({"email": email_addr, "file": file_name})
    return pd.DataFrame(mapping)

def save_distribution_csv(mapping_df):
    """
    Convertit le DataFrame de distribution en CSV pour téléchargement.
    """
    csv_str = mapping_df.to_csv(index=False)
    print("Log (utils): CSV de distribution généré.")
    return csv_str.encode("utf-8")
