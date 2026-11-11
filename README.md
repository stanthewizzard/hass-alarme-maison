# Alarme Maison

Intégration personnalisée Home Assistant : une alarme stable pour les routines, les tableaux de bord et HomeKit, avec sélection manuelle du pilote Diagral.

## Entités

| Entité | Rôle |
|---|---|
| `alarm_control_panel.alarme_maison` | Façade publique |
| `alarm_control_panel.alarme_meudon_centrale` | Pilote cloud existant, inchangé |
| `alarm_control_panel.diagral_local_centrale` | Pilote local existant, inchangé |
| `sensor.alarme_maison_pilote` | Mode réseau vérifié : `local` ou `cloud` |

L'intégration interroge l'API authentifiée `/routing` du Docker Diagral Local toutes les dix secondes. Le Docker consulte OPNsense. Home Assistant ne reçoit aucune clé SSH ni aucun identifiant administrateur du pare-feu.

Une commande provoque une nouvelle vérification du mode, puis un seul appel au service du pilote sélectionné. Aucun renvoi automatique, aucune file de commandes, aucun changement automatique de pilote. Une panne du Docker rend le choix du pilote indisponible, même si le cloud fonctionne encore : la bascule automatique n'est pas implémentée.

L'état affiché est celui du pilote. Une lecture locale trop ancienne rend l'alarme indisponible. Un code local non traduit reste `unknown` ; l'arrêt manuel reste possible si la liaison et la lecture sont fraîches, mais l'armement est refusé tant que l'état n'est pas interprété. L'intégration ne déduit jamais un état de la dernière commande envoyée.

## Installation et configuration

Copier `custom_components/alarme_maison` dans le dossier `custom_components` de Home Assistant, charger le nouveau composant puis ajouter **Alarme Maison** dans les intégrations. Indiquer l'URL du Docker et son jeton existant. Les secrets restent dans le stockage protégé des entrées HA, jamais dans ce dépôt.

Le Docker doit exposer l'API `/routing` de Diagral Local 0.2.0. Le pilote choisi doit être activé dans HA pour répondre ; le routeur n'active ni ne désactive les intégrations. Le mode local/cloud se choisit sur la page de monitoring Docker.

## Migration des consommateurs

Les commandes et lectures des routines générales, de Synthèse et de HomeKit visent la façade. Les rechargements de l'intégration cloud continuent de viser son entité historique et sont conditionnés au pilote `cloud`. Une routine longue cesse ses tentatives si le pilote change pendant son exécution.

Le filtre HomeKit Routine FULL doit viser la façade. La migration de l'accessoire doit préserver les données d'appairage du pont et son AID ; elle n'est pas effectuée automatiquement par cette intégration.

## Validation locale

```powershell
python tests/test_policy.py
```

Les tests ne se connectent ni à HA ni à l'alarme. Ils couvrent le choix local/cloud, les réponses périmées, l'indisponibilité, les codes inconnus, l'envoi unique, l'absence de reprise après timeout et le refus de mettre des commandes en attente.

## Maintenance

Le composant ne modifie aucun fichier du cœur de HA ou des pilotes Diagral. Une mise à jour HA ne remplace pas ce dossier ; la compatibilité avec les API HA doit néanmoins être vérifiée. Le dépôt public est suivi par HACS / Marketplace ; les mises à jour restent manuelles.

## Installation et mises à jour HACS / Marketplace

Ajouter `stanthewizzard/hass-alarme-maison` comme dépôt personnalisé de type intégration. Sur HA 2026.11 et suivantes : Paramètres → Marketplace → Ajouter depuis un lien, puis Installer.

Pour une installation manuelle existante, conserver l’entrée, les entités et les réglages. Le Marketplace reprend la gestion des mêmes fichiers ; ne pas supprimer puis recréer l’intégration. La branche principale est suivie pour les mises à jour. Elles sont proposées et restent à installer manuellement. Suivre l’éventuelle demande de redémarrage de HA. Aucune modification du cœur de HA.
