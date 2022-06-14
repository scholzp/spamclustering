# Konzeption eines Courd basierten Phising Meldesysmtems (BA)
Quelle: Christiansen, Tim Ole. “Konzeption eines Crowd-basierten Phishing-Meldesystems,” n.d., 45.


* Erweiterugn für Thudnerbird
* * ermöglicht Melden von verdächtigen Mails
* * Rückmeldung anhand von 5 Leveln
* Nutzt Fuzzy Hashing für Clustering der Mails
* RESTful API mit einem Flask Server
* Admins können Mails serparat einordnen

# Clustering Spam Emails into Campaigns
Quelle: “Clustering Spam Emails into Campaigns:” In Proceedings of the 1st International Conference on Information Systems Security and Privacy, 90–97. ESEO, Angers, Loire Valley, France: SCITEPRESS - Science and and Technology Publications, 2015. https://doi.org/10.5220/0005244500900097.

* "Clustering is an unsupervised learning task"
* Beschreibt CCTree (Categoric Clustering Tree) Algortihmus zum Klassifizieren der Mails
* * Nutzt Shannon Entropy (purity of node) 
* * Berechnet diese um das beste Attribut zum Aufspalten von einer Menge zu finden
* * Liefert Baum von Attributen 
* * Eine bestimmte Anzahl von DOkumenten befindet sich in einem Knoten
* * Knoten wird aufgespalten wenn vorher definierter Anzahl von Docs überstiegen wird oder purity Grenzwert verletzt wird
* Eher theoretische Betrachtung des Algorithmus
* Komplexität etwas besser als Quadratisch



# Spamcraft: An Inside Look At Spam Campaign Orchestration
Quelle: Kreibich, Christian, Chris Kanich, Kirill Levchenko, Brandon Enright, Geoffrey M Voelker, Vern Paxson, and Stefan Savage. “Spamcraft: An Inside Look At Spam Campaign Orchesand IP itration,” n.d., 9.

* Spam Kampagen zwischen 2007 und 2008
* Untersuchung darauf, wie SPam verändert wird in einer Kampagne
* Am Häufigsten wird ein DIctonary verwedet um Templates zu populaten
* CC-Server schickt templates auf Anfrage von Bot
* Hoher Durchsatz an URLs, da sie schnell in Spam-Datenbanken landen
* Templates von CC-Server enthielten schon Biler
* dauert ca. 5 Tage bis gestohlene Mailadressen Post bekommen
* Hohe Anzahl an verschiedenen Headern
* Domains werden durchschnittlich 5,6 Tage genutzt. Viele Secondlevel Domains
* Von registrierung bis nutzung der Domains ca. 21 Tage


# Clustering Spam Campaigns with Fuzzy Hashing
Quelle:“Chen et al. - 2014 - Clustering Spam Campaigns with Fuzzy Hashing.Pdf,” n.d.

* Dataset: 01.2011-12.2013, 540k Mails
* Nutzen Fuzzy-Hashing, Blockhash hasht block, Rollinghash konkateniert Blockhashes
* * FVN Hash für Blockhashes
* * Alder32 für Rolling Hash
* * Match-degreee bei ca. 85, emprisch bestimmt
* Zeit zwischen erster und letzter Mail empirisch auf 1 Monat festgelegt
* * Nur Mails die in dieses Intervall passen, werden verglichen
* Pairwise comparing of mails
* Bots werden anhand IP identifiziert, erster Mialserver der nicht auf Allow-List steht wird als Bot  identifiziert
* shared IP für shared Botnets: (#IP(A∩B)) / (#minIPs(A,B))
* * wenige Kampagnen teilen sich Botnetze

# Fast and Effective Clustering of Spam Emails Based on Structural Similarity
Quelle: “Sheikhalishahi et al. - 2016 - Fast and Effective Clustering of Spam Emails Based.Pdf,” n.d.

* Nutezn CCTree
* Implementierung nutzt JSoup und [LID Python](http://www.cavar.me/damir/LID/) zum Parsen der Mails und MATlab für CCTree
* Vergleich mit Klassifizierungalgortihmen CLOPE und COBWEB
* Dunn Index für CLuster-Durchmesser, höher ist besser weil homogener, Als Benchmark
* * DIk = min1≤i≤k{min1≤j≤k{ δ(Ci,Cj) / (max1≤t≤k Δt) }}
* Silhoutte als weiterer Benchmark (average dissimilarity eine Datenpunktes mit anderen)
*  * s(i)= (d′(i) − d(i)) / max{d(i),d′(i)} = 1: 1-(d(i)/d'(i)) wenn d(i) < d'(i); 2: 0 wenn d(i) < d'(i); 3: d'(i)/ d'(i) -1 wenn d(i) > d'(i)
* FP-Tree angesporchen
* 




  

