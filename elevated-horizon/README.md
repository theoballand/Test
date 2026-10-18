# Elevated Horizon Studio

CRM local de démonstration : contacts, demandes, missions, brouillons de devis versionnés et préparation documentaire des vols.

## Lancer

Python 3.10+ et bibliothèque standard uniquement. Depuis le dépôt :

```
cd elevated-horizon
python3 server.py
```

Ouvrir http://127.0.0.1:8765 sur la même machine. Cliquer sur « Charger un exemple fictif » pour commencer. Aucun vrai contact ni base n'est fourni dans ce dépôt public.

## Tests

```
python3 -m unittest discover -s elevated-horizon -p 'test_*.py' -v
node --check elevated-horizon/app.js
```

Node est facultatif pour l'application ; cette commande vérifie uniquement la syntaxe JavaScript.

## Données et limites

- SQLite dans `elevated-horizon/private/crm.sqlite3`, exclu du dépôt. Ne jamais committer bases, sauvegardes clients, RIB ou justificatifs.
- Export JSON via « Exporter une sauvegarde ». Pas de restauration par interface dans cette V1 ; conserver aussi une copie de la base serveur arrêté pour restauration technique.
- Les devis sont des brouillons imprimables via le navigateur, pas un système de facturation conforme ou d'émission commerciale.
- Aucun envoi mail, paiement, accès bancaire, autorisation de vol ou contrôle aéronautique automatique.
- Le serveur est limité à 127.0.0.1, sans authentification utilisateur. Ne pas l'exposer à Internet ou via un tunnel public. Il s'agit d'un prototype mono-utilisateur local.
- Le serveur n'intègre pas de coffre documentaire, de galerie de livraison ni le générateur de dossiers du projet local.
- Une case cochée est une déclaration humaine ; même 8/8 ne donne jamais un GO vol automatique.
- L'historique de contact est une zone de notes éditable, pas un journal d'audit inaltérable.
- Les coordonnées du prestataire dans le modèle de devis sont volontairement génériques dans cette copie publique. Les compléter seulement dans une configuration privée avant usage réel.

## Codex cloud

Le code peut être lu, modifié et testé dans un environnement associé à ce dépôt. Aucun script d'installation ni secret n'est nécessaire. L'environnement de développement ne constitue pas un hébergement permanent du CRM : son localhost n'est pas celui du Mac ou de l'iPhone. Prévoir une architecture authentifiée et un stockage durable avant tout accès distant réel.
