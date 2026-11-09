# ☀️ matins

Rappels programmés pour envoyer des messages Instagram à tes proches.

À l'heure choisie (tous les jours, certains jours, ou une seule fois), tu reçois **sur Discord** :
1. un message avec un **lien qui ouvre directement la conversation Instagram** ;
2. le **texte prêt à copier** (appui long → *Copier le texte*).

Tu colles, tu envoies : environ 5 secondes. Le projet n'utilise pas d'API non officielle d'Instagram, donc **aucun risque de blocage de ton compte**.

> 💡 Pour un message ponctuel, Instagram permet aussi de programmer un DM directement dans l'appli : écris le message, **reste appuyé sur Envoyer**, puis choisis la date et l'heure (jusqu'à 29 jours à l'avance).

## Comment ça marche

| Élément | Rôle |
|---|---|
| `docs/index.html` | Interface web (GitHub Pages) pour gérer les rappels |
| `config/messages.json` | Tes rappels (modifiés par l'interface) |
| `.github/workflows/rappels.yml` | GitHub Actions lance la vérification toutes les 5 minutes |
| `scripts/send_reminders.py` | Envoie sur Discord les rappels arrivés à l'heure |
| `state/sent.json` | Retient ce qui a déjà été envoyé aujourd'hui (pas de doublon) |

## Installation (une seule fois)

### 1. Créer le webhook Discord
1. Sur Discord, crée un serveur privé (ou utilise un salon à toi).
2. **Paramètres du salon → Intégrations → Webhooks → Nouveau webhook**, puis **Copier l'URL du webhook**.

### 2. Donner l'URL du webhook à GitHub (en secret)
1. Va sur **https://github.com/CapitaineMax9/matins/settings/secrets/actions**.
2. **New repository secret** : nom `DISCORD_WEBHOOK_URL`, valeur = l'URL copiée.

⚠️ Ne mets jamais cette URL dans un fichier du dépôt : n'importe qui pourrait écrire dans ton salon.

### 3. Activer l'interface web
1. **https://github.com/CapitaineMax9/matins/settings/pages**
2. *Source* : **Deploy from a branch** → branche `main`, dossier `/docs` → **Save**.
3. Quelques minutes plus tard, l'interface est disponible sur **https://capitainemax9.github.io/matins/**.

### 4. Créer un jeton pour l'interface
1. **https://github.com/settings/personal-access-tokens/new**
2. *Repository access* : **Only select repositories** → `matins`.
3. *Permissions* : **Contents** = Read and write, **Actions** = Read and write.
4. Colle le jeton dans l'interface. Il est gardé uniquement dans ton navigateur.

### 5. Tester
Dans l'interface, appuie sur **🔔 Tester Discord** : un message de test doit arriver en environ 1 minute.

## Bon à savoir
- **Retards :** GitHub vérifie toutes les 5 minutes mais peut avoir 5 à 30 minutes de retard aux heures chargées. Préfère des heures « décalées » (7h52 plutôt que 8h00). Un rappel en retard de plus de 2 heures est abandonné pour la journée.
- **Confidentialité :** le dépôt est **public**, donc `config/messages.json` (pseudos et textes) est visible par tout le monde. Pour le rendre privé, il faut savoir que GitHub Pages sur un dépôt privé nécessite un abonnement payant. Tu peux aussi ouvrir `docs/index.html` directement depuis ton ordinateur.
- **Inactivité :** GitHub met en pause les tâches programmées d'un dépôt public sans activité pendant 60 jours. Ici, chaque envoi crée un commit (`state/sent.json`), donc tant que des rappels partent, ça reste actif.
- **Lien Instagram :** `https://ig.me/m/pseudo` ouvre la conversation dans l'appli. Si Discord l'ouvre dans son navigateur intégré, désactive *Paramètres Discord → Discussion → Utiliser le navigateur intégré*.
