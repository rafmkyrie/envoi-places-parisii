import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

def check_smtp_connection(smtp_server, smtp_port, username, password):
    try:
        print(f"Log (email_sender): Connexion à {smtp_server}:{smtp_port} avec {username}")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(username, password)
        server.quit()
        print("Log (email_sender): Connexion SMTP établie avec succès.")
        return True, "Connexion réussie"
    except Exception as e:
        print(f"Log (email_sender): Erreur de connexion SMTP: {e}")
        return False, str(e)

def send_email_message(smtp_server, smtp_port, username, password, recipient, subject, body, attachment_path, is_html=False):
    try:
        print(f"Log (email_sender): Préparation de l'email pour {recipient}")
        # Créer le message
        msg = MIMEMultipart()
        msg["From"] = username
        msg["To"] = recipient
        msg["Subject"] = subject
        
        # Déterminer le type de contenu (texte simple ou HTML)
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))

        # Ajouter la pièce jointe
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{attachment_path.split("/")[-1]}"')
        msg.attach(part)

        # Envoi de l'email
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        print(f"Log (email_sender): Email envoyé à {recipient}")
        return True, "Email envoyé"
    except Exception as e:
        print(f"Log (email_sender): Erreur lors de l'envoi à {recipient}: {e}")
        return False, str(e)