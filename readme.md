Repo di sviluppo della parte python della TableAPI di WindFlow.

L'API python per ora si divide in tre componenti "api", "codegen" e "runtime".

Attualmente api è in uno stato avanzato di sviluppo e riceve soltanto alcuni ritocchi alla serializzazione del json in base ai livelli inferiori.
Comunque ci sono aggiunte che si potrebbero fare ma è funzionante e funzionale.
Per ora è l'unica parte coperata dalla documentazione (attenzione è lunga).

La componente codegen è attualmente in sviluppo e vede per ora realizzati una buona parte dei template jinja che permettono di generare gli struct (con hash e costruttori di finestra se necessari) rappresentanti gli schemi dei flussi, traduzione delle espressioni da json a cpp e inserimento di tali espressioni nelle lambda richieste dai builder.
Attualmente (26/08/26) è in sviluppo la visita del grafo che chiama i meccanismi sopra-citati, la scrittura dei template per i builder e per il main.

La componente di runtime è per ora vuota.

In examples/ si trovano esempi di query (simple.py, prova.py, group.py) e di generazione/traduzione del codice/espressioni (expr.py, builders.py, lambdas.py, structs.py).

Nella versione completa il metodo execute dovrà chiamare il main di codegen a seguito di una fork, questo attualmente non è ancora implementato dunque alcuni esempi non fanno altro che generare il json se non è esplicitata la chiamata al codegen.
