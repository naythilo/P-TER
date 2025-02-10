package org.example;

import org.eclipse.rdf4j.federated.FedXConfig;
import org.eclipse.rdf4j.federated.FedXFactory;
import org.eclipse.rdf4j.query.BindingSet;
import org.eclipse.rdf4j.query.TupleQuery;
import org.eclipse.rdf4j.query.TupleQueryResult;
import org.eclipse.rdf4j.repository.Repository;
import org.eclipse.rdf4j.repository.RepositoryConnection;

import java.nio.file.Files;
import java.nio.file.Paths;

public class Virtuoso {

    public static void main(String[] args) throws InterruptedException {
        String input = "";

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--input")) {
                input = args[i + 1];
            }
        }

        FedXConfig config = new FedXConfig().withLogQueries(true);
        Repository repository = FedXFactory.newFederation()
                .withConfig(config)
                .create();
        long startTime = System.nanoTime();

        try (RepositoryConnection conn = repository.getConnection()) {

            // Lire la requête SPARQL depuis le fichier d'entrée
        String query = "";
        try {
            query = new String(Files.readAllBytes(Paths.get(input)));
        } catch (Exception e) {
            System.err.println("Error reading the input file: " + e.getMessage());
            System.exit(1);
        }

        // Afficher la requête pour débogage
        System.out.println("Loaded SPARQL Query: \n" + query);


            TupleQuery tq = conn.prepareTupleQuery(query);
            try (TupleQueryResult tqRes = tq.evaluate()) {
                int count = 0;


                while (tqRes.hasNext()) {
                    BindingSet b = tqRes.next();
                    System.out.println(b);
                    count++;

                }

                System.out.println("Results: " + count);

                // Enregistrement du temps de fin de la requête
                long endTime = System.nanoTime();

                // Calcul du temps écoulé en secondes
                long duration = (endTime - startTime) / 1000000; // En millisecondes

                // Affichage du temps d'exécution
                System.out.println("Execution Time: " + duration + " ms");
            }
        }

        // Fermez la fédération après utilisation
        repository.shutDown();
    }
}
