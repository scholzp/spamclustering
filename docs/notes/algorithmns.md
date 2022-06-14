# Normalisierung
* alles nach UFT-8
* Stemmer, zBsp Proter Stemmer nutzen
* Eventuell Synonyme beachten (Dictonary?)
* Optisch ähnliche Zeichen aus verschiedenen Alphabeten beachten?


# Klassifizierungs-Algortihmen

## CCTree
#### Klasse
* Decision Trees

#### Quellen: 

* “Clustering Spam Emails into Campaigns:” In Proceedings of the 1st International Conference on Information Systems Security and Privacy, 90–97. ESEO, Angers, Loire Valley, France: SCITEPRESS - Science and and Technology Publications, 2015. https://doi.org/10.5220/0005244500900097.
* “Sheikhalishahi et al. - 2016 - Fast and Effective Clustering of Spam Emails Based.Pdf,” n.d.

#### Algorithmus
* Object wird von einer Menge kategroscher Attribute beschrieben
* Für jedes Attribut wird gebranched, je nach konkretem Wert
* Attribut mit maximaler Shannon Entropie wird zum branchen gewählt
* Purity function basierend auf Shannon Entropie für jeden Knoten, welche Homogenität bestimmt
* Wenn Purity einen Grenzwert (Threshold) übersteigt, wird Knoten als Blatt markiert
* 


## FPTree
#### Klasse
* Tree
#### Quellen
* Dinh, Son, Taher Azeb, Francis Fortin, Djedjiga Mouheb, and Mourad Debbabi. “Spam Campaign Detection, Analysis, and Investigation.” Digital Investigation 12 (March 2015): S12–21. https://doi.org/10.1016/j.diin.2015.01.006.
* Han, Jiawei, Jian Pei, Yiwen Yin, and Runying Mao. “Mining Frequent Patterns without Candidate Generation: A Frequent-Pattern Tree Approach.” Data Mining and Knowledge Discovery 8, no. 1 (January 2004): 53–87. https://doi.org/10.1023/B:DAMI.0000005258.31418.83.

#### Algorithmus
* frequency mining 
* prefix tree
* häufig vorkommende attribute weiter oben im Baum

## CLOBE
####Quellene

* “CLOBE.Pdf,” n.d.


#### Algorithmus
* Basiert auf geometrischen Eigenschaften der Cluster
* Histogram zum Darstellen des Zusammenhangs eines Clusters
* Breite/Höhe Verhaätlnis eines Clusters dafiert Zusammenhang
* Wird genutzt um zu entschieden, wann ein Cluster aufgespalten wird
* 


## Fuzzy Hashing
####Quellen:

* “Chen et al. - 2014 - Clustering Spam Campaigns with Fuzzy Hashing.Pdf,” n.d.

#### Algorithmus
* Zwei Hashfunktionen: Blockhash und Rollinghash
* Dokument wird in Blöcker geteilt und gehasht
* Blockhashfunktionen: FVN Hash
* Rollinghash für das Bilden eines Hashwertes über die Hashwerte
* Rollinghashfunktionen: ALDER32
* Mathdegree als Threshold zum Entscheiden über Clusterzugehörigkeit
* 


## Perceptual Hashses
#### Quellen
* Monga, V., A. Banerjee, and B.L. Evans. “A Clustering Based Approach to Perceptual Image Hashing.” IEEE Transactions on Information Forensics and Security 1, no. 1 (March 2006): 68–79. https://doi.org/10.1109/TIFS.2005.863502.
*Wen Zhen-kun, Zhu Wei-zong, Ouyang Jie, Liu Peng-fei, Du Yi-hua, Zhang Meng, and Gao Jin-hua. “A Robust and Discriminative Image Perceptual Hash Algorithm.” In 2010 Fourth International Conference on Genetic and Evolutionary Computing, 709–12. Shenzhen: IEEE, 2010. https://doi.org/10.1109/ICGEC.2010.180.
*Zauner, Christoph. “Implementation and Benchmarking of Perceptual Image Hash Functions,” n.d., 107.

#### Algorithmus
* Feature Vektor wird aus Bild axtrahiert
* Vektor wird in einzelnen Wert komprimiert
* Hash


## AI/ ML based approaches
#### Quellen
* Gupta, Brij B., Aakanksha Tewari, Ivan Cvitić, Dragan Peraković, and Xiaojun Chang. “Artificial Intelligence Empowered Emails Classifier for Internet of Things Based Systems in Industry 4.0.” Wireless Networks 28, no. 1 (January 2022): 493–503. https://doi.org/10.1007/s11276-021-02619-w.
* * Auf Basis von Web Soam

* Goh, Kwang Leng, and Ashutosh Kumar Singh. “Comprehensive Literature Review on Machine Learning Structures for Web Spam Classification.” Procedia Computer Science 70 (2015): 434–41. https://doi.org/10.1016/j.procs.2015.10.069.#
* Adewole, Kayode Sakariyah, Tao Han, Wanqing Wu, Houbing Song, and Arun Kumar Sangaiah. “Twitter Spam Account Detection Based on Clustering and Classification Methods.” The Journal of Supercomputing 76, no. 7 (July 2020): 4802–37. https://doi.org/10.1007/s11227-018-2641-x.


#### Algorithmus
* Preprocessing mit Feature Extraction
* Extrahierte Feuatures werden mit Classifier gewichtet
* Ergbnis von Classifiern liefert Klassifizierung
* K-means

#### Classifier
* NB (Naivce Bayes)
* SVM (Support Vector machines)
* MLP (Multi Layer Perceptron Network)
* KNN (K nearest Neighbours)
* DT (Decision Trees)
* RF (Random Forest)

# Benchmarking
#### F measure
