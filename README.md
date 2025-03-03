# PROJET TER

## Installation

### jena-fuseki
- pour installer jena fuseki, aller sur ce site :
https://jena.apache.org/download/

- télécharger le fichier `apache-jena-fuseki-XXX.zip`

- dézipper le fichier
- se rendre avec le terminal dans le dossier
- lancer le serveur avec la commande suivante :
```bash 
./fuseki-server
```

- Si le port est déja utilisé, il faut changer le port dans le fichier `fuseki-server` ou kill le processus qui utilise le port
- Créer un dataset
- aller dans query
- Mettez votre requete


### virtuoso
- aller sur : https://github.com/openlink/virtuoso-opensource
- télécharger le installer packages adapté à votre système
- installer le
- aller sur : https://zenodo.org/records/12204740
- télécharger le fichier `fedshop-virtuoso.db` et `fedshop-virtuoso.ini`
- renommer le fichier `fedshop-virtuoso.ini` en 'virtuoso.ini'
- aller dans le dossier d'installation de virtuoso 'Virtuoso Open Source Edition v7.2.app/Contents/virtuoso-opensource/database'
- suprimer le fichier virtuoso.ini et remplacer le par celui que l'on viens de télécharger
- ajouter le fichier `fedshop-virtuoso.db`
- lancer virtuoso
- pour tester aller dans le navigateur et taper : `http://localhost:8890/sparql`
- tester la commande suivante :
```sparql
SELECT DISTINCT ?graph WHERE {
  GRAPH ?graph { ?s ?p ?o }
}
```

### Lancer les requetes
- aller dans Virtuoso.java 
- allumer virtuoso
- executer le script
- aller sur fuseki
- executer la query


### executer le snakemake

il faut d'abord installer hefquin pour cela aller dans Workspace (cd ..)
- git clone https://github.com/LiUSemWeb/HeFQUIN.git
si erreur jdk < 17
--sdk install java 17.0.0-tem
-mvn clean install
-mvn package

- configuer vos options dans `Snakefile` (installer tout les outils avant en mettant DO_INSTALL A TRUE)
- faire ```snakemake``` dans le terminal
(pour config FedX, démarrer avec vscode le fichier Virtuoso.java avec le bouton run en haut a droite et en bas a droite accepter le message, ensuite lancer le snakefile)

si le snakemake ne run aucune query, supprimez le fichier output





#reste

hefquin
mvn clean install
sdk install java 17.0.0-tem
./bin/hefquin --federationDescription /workspaces/HeFQUIN/fedeation.ttl --file q05d.sparql --time


apache
go bin
./sparql --query /workspaces/P-TER/queries/q05d.sparql --time

fedx
/usr/bin/env /opt/java/11.0.14/bin/java @/tmp/cp_epia4f4tkru96q17baqr1dz53.argfile org.example.Virtuoso --input /workspaces/P-TER/queries/q05d.sparql


fedup w fedx
git clone https://github.com/GDD-Nantes/fedup.git
cd fedup
mvn clean install -Dmaven.test.skip=true
sdk default java 21.0.5-ms  
min java 21
dans le target 
java -jar ../fedup/target/fedup.jar -e FedX -f /workspaces/P-TER/queries/qex.sparql -s fedshop200-h0 -x -m='(e) -> "http://localhost:8890/sparql?default-graph-uri="+(e.substring(0, e.length() ))'