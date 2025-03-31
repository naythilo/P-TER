# PROJET TER

## Installation

### HefQuin + FedUp
il faut d'abord installer HeFQUIN Fraw, disponible à l'adresse suivante : 
https://github.com/GDD-Nantes/HeFQUIN-FRAW/tree/hefquin_with_fedup

Ne pas oublier de changer de branche est aller sur "hefquin with fedup"
-> appliquer le tuto
-> changer [YOUR_ENDPOINT_URL] par "localhost:8890\/sparql"

Si erreur clonage git : 
git clone https://token@github.com/GDD-Nantes/HeFQUIN-FRAW.git
token = token github généré

Si erreur jdk < 17
-> sdk default java 21.0.5-ms  


### FedX

aller dans /workspaces/P-TER/src/main/java/org/example/Virtuoso.java
lancer le programme avec la fléche en haut a droite (a faire a chaque redémarage du codespace)
Recuperer la valeur ressemblant a ceci : "@/tmp/cp_epia4f4tkru96q17baqr1dz53.argfile" dans le terminal (commande d'éxécution du fichier)
La remplacer dans le Snakefile a la ligne : 239

### Jena + virtuoso

Dans rule all tout décommenter
Mettre la valeur DO_INSTALL a True et les autres a False
dans le terminal, dans le fichier a la racine écrire "snakemake"

### Dépendances
Il y aura des erreurs, il faudra installer des dépendances avec pip install
  notamment :
  - pip install click (ou cli)
  - pip install SPARQLWrapper


## Executer le snakemake

- configuer vos options dans `Snakefile` (installer tout les outils avant en mettant DO_INSTALL A TRUE)
- faire ```snakemake -c 1``` dans le terminal ou '''snakemake''' si vous n'utilisez pas fedup
(pour config FedX, démarrer avec vscode le fichier Virtuoso.java avec le bouton run en haut a droite et en bas a droite accepter le message, ensuite lancer le snakefile)

si le snakemake ne run aucune query, supprimez le fichier output

## Executer les commandes a la main

 - Verifier si virtuoso est lancer : 
  ps -edf | grep virtuoso

 - Lancer Jena :
    - aller dans jena : /workspaces/P-TER/apache-jena-4.9.0/bin
    -  ./sparql --query path/to/query.sparql --time
- Lancer FedX
  - /usr/bin/env /opt/java/11.0.14/bin/java @/tmp/cp_epia4f4tkru96q17baqr1dz53.argfile org.example.Virtuoso --input /workspaces/P-TER/queries/q05d.sparql

  - changer la valeur '@/tmp/cp_epia4f4tkru96q17baqr1dz53.argfile' si besoin

- Lancer FeduP avec FedX
  - se rendre dans le dossier ou se trouve fedshop200-h0 (si installation suivi auparavant, il se trouve dans Hefquin-Fraw/summaries)
  - java -jar ../fedup/target/fedup.jar -e FedX -f path/to/query.sparql -s fedshop200-h0 -x -m='(e) -> "http://localhost:8890/sparql?default-graph-uri="+(e.substring(0, e.length() ))'

  -Pour lancer avec Jena change FedX par Jena

-Lancer HefQuin
  -Aller dans /workspaces/HeFQUIN-FRAW
  -./bin/hefquin --federationDescription fedshop200.ttl --confDescr DefaultEngineConfForRSA.ttl --file path/to/query.sparql --time --results=JSON 

-Lancer FedUp HefQuin
  -Aller dans /workspaces/HeFQUIN-FRAW
  -./bin/hefquin --federationDescription fedshop200.ttl --confDescr DefaultEngineWithFedupConfForFedshop200.ttl --file path/to/query.sparql --time --results=JSON --printQueryProcStats




curl -X POST "http://localhost:8890/sparql" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "query@/workspaces/P-TER/queries/q12fex.sparql"