import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration des logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# États de la conversation
(
    ACCUEIL,
    CONNEXION_PROBLEME,
    CONNEXION_OUBLI,
    CONNEXION_RESOLU,
    COMMANDE_SUIVI,
    COMMANDE_NUMERO,
    ACHAT_GUIDE,
    AUTRE_PROBLEME,
    ESCALADE
) = range(9)

# Stockage temporaire
user_data_store = {}

class PandoraBot:
    """Bot de support client Pandora - Niveau 1"""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Message d'accueil"""
        keyboard = [
            [InlineKeyboardButton("🔹 Je n'arrive pas à me connecter", callback_data="connexion")],
            [InlineKeyboardButton("🔹 Je n'ai pas reçu ma commande", callback_data="commande")],
            [InlineKeyboardButton("🔹 Je souhaite effectuer un achat", callback_data="achat")],
            [InlineKeyboardButton("🔹 Je ne comprends pas la plateforme", callback_data="autre")],
            [InlineKeyboardButton("🔹 Contacter un conseiller", callback_data="escalade")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Bonjour 👋\n\n"
            "Bienvenue au support Pandora.\n"
            "Quel problème rencontrez-vous aujourd'hui ?",
            reply_markup=reply_markup
        )
        return ACCUEIL

    @staticmethod
    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Gestionnaire des boutons"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if user_id not in user_data_store:
            user_data_store[user_id] = {}
        
        if data == "connexion":
            return await PandoraBot.connexion_probleme(update, context)
        elif data == "commande":
            return await PandoraBot.commande_suivi(update, context)
        elif data == "achat":
            return await PandoraBot.achat_guide(update, context)
        elif data == "autre":
            return await PandoraBot.autre_probleme(update, context)
        elif data == "escalade":
            return await PandoraBot.escalade_conseiller(update, context)
        elif data == "oublie":
            return await PandoraBot.connexion_oublie(update, context)
        elif data == "resolu_oui":
            await query.edit_message_text("✅ Super ! N'hésitez pas si vous avez d'autres questions.")
            return ConversationHandler.END
        elif data == "resolu_non":
            keyboard = [[InlineKeyboardButton("📞 Parler à un conseiller", callback_data="escalade")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Je suis désolé de ne pas avoir pu résoudre votre problème.\n\n"
                "Souhaitez-vous parler à un conseiller ?",
                reply_markup=reply_markup
            )
            return ESCALADE
        elif data == "suivi_oui":
            await query.edit_message_text(
                "📦 Veuillez saisir votre numéro de suivi :\n\n"
                "_(ex: PD123456789FR)_"
            )
            return COMMANDE_NUMERO
        elif data == "suivi_non":
            await query.edit_message_text(
                "📋 Veuillez fournir votre numéro de commande :\n\n"
                "_(ex: #CMD-2024-001)_"
            )
            return COMMANDE_NUMERO
        elif data == "escalade_ok":
            await query.edit_message_text(
                "📞 Un conseiller va vous contacter dans les plus brefs délais.\n\n"
                "Merci de votre patience 🙏"
            )
            logger.info(f"Ticket créé pour l'utilisateur {user_id}")
            return ConversationHandler.END
        
        return ACCUEIL

    # ============= CAS 1 : PROBLÈME DE CONNEXION =============
    @staticmethod
    async def connexion_probleme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Sous-menu problème de connexion"""
        query = update.callback_query
        keyboard = [
            [InlineKeyboardButton("🔹 J'ai oublié mon mot de passe", callback_data="oublie")],
            [InlineKeyboardButton("🔹 Mon compte est bloqué", callback_data="bloque")],
            [InlineKeyboardButton("🔹 Je ne reçois pas le code", callback_data="code")],
            [InlineKeyboardButton("🔹 Mon email est refusé", callback_data="email")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Pouvez-vous préciser le problème ?",
            reply_markup=reply_markup
        )
        return CONNEXION_PROBLEME

    @staticmethod
    async def connexion_oublie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Procédure mot de passe oublié"""
        query = update.callback_query
        
        keyboard = [
            [InlineKeyboardButton("✅ Oui", callback_data="resolu_oui")],
            [InlineKeyboardButton("❌ Non", callback_data="resolu_non")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔑 Voici la procédure :\n\n"
            "1. Cliquez sur « Mot de passe oublié »\n"
            "2. Saisissez votre adresse e-mail\n"
            "3. Consultez votre boîte mail\n\n"
            "Le problème est-il résolu ?",
            reply_markup=reply_markup
        )
        return CONNEXION_RESOLU

    # ============= CAS 2 : COMMANDE NON REÇUE =============
    @staticmethod
    async def commande_suivi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Vérification du suivi de commande"""
        query = update.callback_query
        keyboard = [
            [InlineKeyboardButton("✅ Oui", callback_data="suivi_oui")],
            [InlineKeyboardButton("❌ Non", callback_data="suivi_non")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📦 Avez-vous reçu un numéro de suivi ?",
            reply_markup=reply_markup
        )
        return COMMANDE_SUIVI

    @staticmethod
    async def commande_numero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Réception du numéro de suivi/commande"""
        user_id = update.effective_user.id
        numero = update.message.text
        
        user_data_store[user_id]['numero'] = numero
        
        keyboard = [[InlineKeyboardButton("📞 Contacter un conseiller", callback_data="escalade_ok")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔍 Merci ! Nous vérifions les informations pour :\n"
            f"`{numero}`\n\n"
            "Souhaitez-vous qu'un conseiller examine votre dossier ?",
            reply_markup=reply_markup
        )
        return ESCALADE

    # ============= CAS 3 : AIDE À L'ACHAT =============
    @staticmethod
    async def achat_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Guide d'achat"""
        query = update.callback_query
        
        await query.edit_message_text(
            "🛒 Je peux vous guider :\n\n"
            "1️⃣ Choisissez un produit\n"
            "2️⃣ Ajoutez-le au panier\n"
            "3️⃣ Validez votre commande\n"
            "4️⃣ Sélectionnez votre mode de paiement\n"
            "5️⃣ Confirmez votre adresse de livraison\n\n"
            "Avez-vous besoin d'aide sur une étape particulière ?\n"
            "Décrivez votre question ci-dessous ⬇️"
        )
        return ACHAT_GUIDE

    # ============= CAS 4 : PROBLÈME NON RÉPERTORIÉ =============
    @staticmethod
    async def autre_probleme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Problème non répertorié"""
        query = update.callback_query
        
        await query.edit_message_text(
            "🔍 Décrivez votre problème en quelques mots :\n\n"
            "_(Ex: Je ne comprends pas comment utiliser mon compte)_"
        )
        return AUTRE_PROBLEME

    @staticmethod
    async def traiter_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Traitement des messages texte"""
        user_id = update.effective_user.id
        message = update.message.text.lower()
        
        # Analyse par mots-clés simple
        keywords = {
            "compte": "Je vois que vous avez un problème avec votre compte.",
            "paiement": "Je comprends, le paiement peut être bloqué.",
            "produit": "Souhaitez-vous des informations sur un produit ?",
            "livraison": "La livraison peut prendre 3 à 5 jours ouvrés."
        }
        
        reponse = "Je n'ai pas bien compris. Pouvez-vous reformuler ?"
        for mot, rep in keywords.items():
            if mot in message:
                reponse = rep
                break
        
        keyboard = [[InlineKeyboardButton("📞 Contacter un conseiller", callback_data="escalade_ok")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{reponse}\n\n"
            "Si vous préférez, vous pouvez contacter un conseiller :",
            reply_markup=reply_markup
        )
        return ESCALADE

    # ============= ESCALADE =============
    @staticmethod
    async def escalade_conseiller(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Escalade vers un conseiller"""
        query = update.callback_query
        
        keyboard = [[InlineKeyboardButton("✅ Confirmer", callback_data="escalade_ok")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📞 Vous souhaitez parler à un conseiller.\n\n"
            "Cliquez sur Confirmer pour être mis en relation.",
            reply_markup=reply_markup
        )
        return ESCALADE

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Annuler et terminer la conversation"""
        await update.message.reply_text(
            "👋 À bientôt ! N'hésitez pas à revenir si besoin."
        )
        return ConversationHandler.END

# ============= MAIN =============
def main():
    """Lancement du bot"""
    # Récupérer le token depuis les variables d'environnement
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("❌ ERREUR: Token non trouvé !")
        print("📝 Créez un fichier .env avec : TELEGRAM_TOKEN=votre_token")
        print("📝 Ou définissez la variable d'environnement TELEGRAM_TOKEN")
        return
    
    print("✅ Token chargé avec succès !")
    
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", PandoraBot.start)],
        states={
            ACCUEIL: [CallbackQueryHandler(PandoraBot.button_handler)],
            CONNEXION_PROBLEME: [CallbackQueryHandler(PandoraBot.button_handler)],
            CONNEXION_OUBLI: [CallbackQueryHandler(PandoraBot.button_handler)],
            CONNEXION_RESOLU: [CallbackQueryHandler(PandoraBot.button_handler)],
            COMMANDE_SUIVI: [CallbackQueryHandler(PandoraBot.button_handler)],
            COMMANDE_NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, PandoraBot.commande_numero)],
            ACHAT_GUIDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, PandoraBot.traiter_message)],
            AUTRE_PROBLEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, PandoraBot.traiter_message)],
            ESCALADE: [CallbackQueryHandler(PandoraBot.button_handler)],
        },
        fallbacks=[CommandHandler("cancel", PandoraBot.cancel)],
    )
    
    application.add_handler(conv_handler)
    
    print("🤖 Bot Pandora démarré...")
    print("📱 Allez sur Telegram et envoyez /start à votre bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()