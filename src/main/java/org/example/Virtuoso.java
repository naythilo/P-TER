package org.example;

import org.eclipse.rdf4j.federated.FedXConfig;
import org.eclipse.rdf4j.federated.FedXFactory;
import org.eclipse.rdf4j.query.BindingSet;
import org.eclipse.rdf4j.query.TupleQuery;
import org.eclipse.rdf4j.query.TupleQueryResult;
import org.eclipse.rdf4j.repository.Repository;
import org.eclipse.rdf4j.repository.RepositoryConnection;

import com.fasterxml.jackson.databind.ObjectMapper;


import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class Virtuoso {

    public static void main(String[] args) throws InterruptedException {
        String input = "";
        String jsonPath = "";
        String csvPath = "";

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--input")) {
                input = args[i + 1];
            }
            if (args[i].equals("--outputJson")) {
                jsonPath = args[i + 1];
            }
            if (args[i].equals("--outputCsv")) {
                csvPath = args[i + 1];
            }
        }

        FedXConfig config = new FedXConfig().withLogQueries(true).withEnforceMaxQueryTime(60000);;
        Repository repository = FedXFactory.newFederation()
                .withConfig(config)
                .create();
        
        List<Map<String, String>> solutions = new ArrayList<>();

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
            //System.out.println("Loaded SPARQL Query: \n" + query);


            TupleQuery tq = conn.prepareTupleQuery(query);
            long startTime = System.currentTimeMillis();
            try (TupleQueryResult tqRes = tq.evaluate()) {
                int count = 0;


                while (tqRes.hasNext()) {
                    BindingSet b = tqRes.next();
                    System.out.println(b);
                    count++;

                    // Ajouter chaque solution à la liste
                    Map<String, String> solutionMap = new HashMap<>();
                    b.getBindingNames().forEach(binding -> solutionMap.put(binding, b.getValue(binding).toString()));
                    solutions.add(solutionMap);

                }

                System.out.println("Results: " + count);

                // Enregistrement du temps de fin de la requête
                long endTime = System.currentTimeMillis();
                
                // Calcul du temps écoulé en secondes
                float duration = endTime - startTime; // En millisecondes
                System.out.println("before"+duration);
                duration =  duration / 1000;
                // Affichage du temps d'exécution
                System.out.println("Execution Time: " + duration + " sec");

                generateJson(solutions, jsonPath);

                generateCsv(csvPath, duration, count);


            }
        }

        // Fermez la fédération après utilisation
        repository.shutDown();
    }


    // Générer le fichier JSON avec les résultats
    private static void generateJson(List<Map<String, String>> solutions, String jsonPath) {
        ObjectMapper objectMapper = new ObjectMapper();
        try {
            System.out.println(jsonPath);
            // Sauvegarder les résultats en JSON à l'emplacement spécifié par jsonPath
            objectMapper.writeValue(new File(jsonPath), solutions);
        } catch (IOException e) {
            System.err.println("Error writing JSON file: " + e.getMessage());
        }
    }

    // Générer le fichier CSV avec les métriques
    private static void generateCsv(String csvPath, float executionTime, int numSolutions) {
        try (FileWriter writer = new FileWriter(csvPath, true)) {
            // Écrire les métriques dans le fichier CSV
            writer.append("status,TotalExecutionTime,nbResult,planningTime,executionTime\n");
            writer.append("ok,"+executionTime+","+numSolutions+",None,None");
        } catch (IOException e) {
            System.err.println("Error writing CSV file: " + e.getMessage());
        }
    }
}
