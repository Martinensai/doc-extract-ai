-- schema.sql
-- DDL (Data Definition Language) pour le schéma DocuExtract Benin

-- Table 1/3: decrets (Informations principales du document)
CREATE TABLE IF NOT EXISTS decrets (
    id_decret SERIAL PRIMARY KEY,
    numero_complet VARCHAR(50) NOT NULL UNIQUE,
    type_document VARCHAR(20) NOT NULL,
    date_publication DATE NOT NULL,
    ministere_concerne VARCHAR(255) NOT NULL,
    objet TEXT NOT NULL,
    checksum VARCHAR(64) UNIQUE,
    chemin_fichier_local VARCHAR(500) NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_decrets_numero ON decrets (numero_complet);

-- Table 2/3: decret_articles (Contenu textuel détaillé)
CREATE TABLE IF NOT EXISTS decret_articles (
    id_article SERIAL PRIMARY KEY,
    id_decret INT NOT NULL,
    numero_article VARCHAR(20) NOT NULL,
    contenu TEXT NOT NULL,
    UNIQUE (id_decret, numero_article),
    CONSTRAINT fk_decret_art
        FOREIGN KEY (id_decret)
        REFERENCES decrets (id_decret)
        ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_articles_decret_id ON decret_articles (id_decret);

-- Table 3/3: decret_signataires (Signataires et leurs fonctions)
CREATE TABLE IF NOT EXISTS decret_signataires (
    id_signature SERIAL PRIMARY KEY,
    id_decret INT NOT NULL,
    nom_signataire VARCHAR(150) NULL,
    fonction_signataire VARCHAR(255) NOT NULL,
    UNIQUE (id_decret, nom_signataire),
    CONSTRAINT fk_decret_sign
        FOREIGN KEY (id_decret)
        REFERENCES decrets (id_decret)
        ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_signataires_decret_id ON decret_signataires (id_decret);