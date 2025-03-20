## Installation sur 

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