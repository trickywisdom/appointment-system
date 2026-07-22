BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "appointments" (
	"id"	INTEGER,
	"customer_id"	INTEGER NOT NULL,
	"datetime"	TEXT NOT NULL,
	"services"	TEXT NOT NULL,
	"duration"	INTEGER NOT NULL DEFAULT 20,
	"notes"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("customer_id") REFERENCES "customers"("id")
);
CREATE TABLE IF NOT EXISTS "customers" (
	"id"	INTEGER,
	"first_name"	TEXT NOT NULL,
	"last_name"	TEXT NOT NULL,
	"phone"	TEXT NOT NULL UNIQUE,
	"email"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "appointments" VALUES (1,1,'2025-05-28 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (4,1,'2025-05-29 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (6,3,'2025-05-29 18:40','Κούρεμα',60,'');
INSERT INTO "appointments" VALUES (8,2,'2025-05-30 11:20','Βάψιμο',40,'Σημείωση για βάψιμο');
INSERT INTO "appointments" VALUES (10,2,'2025-05-27 10:00','Κούρεμα',60,'Έχει ζητήσει για το καινούργιο ΤΝ ψαλίδι');
INSERT INTO "appointments" VALUES (12,4,'2025-05-19 11:20','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (13,4,'2025-05-20 10:00','Κούρεμα',20,'a a a ');
INSERT INTO "appointments" VALUES (14,4,'2025-05-15 13:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (15,4,'2025-05-25 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (16,4,'2025-04-28 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (17,4,'2025-05-29 19:40','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (18,4,'2025-05-29 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (19,4,'2025-06-01 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (21,4,'2025-06-01 18:20','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (22,4,'2025-06-06 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (23,4,'2025-05-10 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (24,4,'2025-06-08 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (25,4,'2025-06-07 12:00','Χτένισμα',20,'Μια μικρή σημείωση φφσδασφ ασδφσαδ σδαφασδφ αδσφσδαφ ασδδφσδαφ δσφδαφ σδαφφ ασδφ');
INSERT INTO "appointments" VALUES (26,4,'2025-05-29 13:00','Βάψιμο',40,'');
INSERT INTO "appointments" VALUES (27,4,'2025-06-04 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (28,4,'2025-05-10 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (30,4,'2025-05-09 13:00','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (31,4,'2025-06-08 11:40','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (37,1,'2025-06-02 14:00','Βάψιμο',60,'');
INSERT INTO "appointments" VALUES (38,1,'2025-05-27 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (39,4,'2025-06-02 16:00','Βάψιμο',60,'');
INSERT INTO "appointments" VALUES (40,3,'2025-06-02 18:00','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (41,2,'2025-06-01 18:00','Κούρεμα',20,'κούρεμα!');
INSERT INTO "appointments" VALUES (42,2,'2025-06-01 18:40','Χτένισμα',20,'Χτένισμα!');
INSERT INTO "appointments" VALUES (43,2,'2025-06-03 10:00','Βάψιμο',60,'');
INSERT INTO "appointments" VALUES (45,4,'2025-06-01 12:20','Κούρεμα',60,'');
INSERT INTO "appointments" VALUES (48,2,'2025-06-01 10:00','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (50,3,'2025-06-03 12:00','Χτένισμα',40,'');
INSERT INTO "appointments" VALUES (51,2,'2025-06-04 14:20','Βάψιμο',60,'');
INSERT INTO "appointments" VALUES (52,3,'2025-06-04 17:00','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (53,4,'2025-06-04 18:00','Βάψιμο',60,'');
INSERT INTO "appointments" VALUES (54,1,'2025-06-05 11:00','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (55,1,'2025-06-02 10:20','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (56,1,'2025-06-02 10:40','Κούρεμα',20,'');
INSERT INTO "appointments" VALUES (61,8,'2025-06-02 13:40','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (62,12,'2025-06-02 13:20','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (63,3,'2025-06-03 10:00','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (65,14,'2025-06-03 10:40','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (66,4,'2025-06-03 11:00','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (68,2,'2025-06-05 16:00','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (70,4,'2025-06-04 10:40','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (78,1,'2025-06-06 11:40','Κούρεμα',40,'Σημείωση!@!');
INSERT INTO "appointments" VALUES (81,20,'2025-06-10 18:00','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (82,21,'2025-06-10 18:40','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (83,1,'2025-06-10 10:00','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (84,22,'2025-06-11 10:00','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (85,22,'2025-06-11 10:40','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (89,22,'2025-06-11 11:20','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (90,22,'2025-06-11 12:00','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (91,2,'2025-06-11 12:40','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (92,2,'2025-06-11 13:20','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (93,2,'2025-06-11 14:00','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (94,22,'2025-06-11 14:40','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (96,3,'2025-06-11 16:00','Βάψιμο',60,'');
INSERT INTO "appointments" VALUES (97,23,'2025-06-11 17:00','Χτένισμα',20,'');
INSERT INTO "appointments" VALUES (98,4,'2025-06-11 17:20','Κούρεμα',40,'');
INSERT INTO "appointments" VALUES (99,2,'2025-06-12 18:00','Βάψιμο',60,'');
INSERT INTO "appointments" VALUES (100,2,'2025-06-17 13:00','Κούρεμα',40,'');
INSERT INTO "customers" VALUES (1,'Σπύρος','Τρίμης','6947474747','std168336@ac.eap.gr');
INSERT INTO "customers" VALUES (2,'Χριστίνα','Καραγιάννη','6947373737','xristina@gmail.not');
INSERT INTO "customers" VALUES (3,'Αλεξάνδρα','Παπαχατζηαλεξάνδρουουου','6947000000','alexia#gmail.com');
INSERT INTO "customers" VALUES (4,'Λεωνίδας','Παπαχλιμίντζος','1010101010','α');
INSERT INTO "customers" VALUES (7,'Γ','Γ','Γ','Γ');
INSERT INTO "customers" VALUES (8,'Δ','Δ','Δ','Δ');
INSERT INTO "customers" VALUES (9,'Ε','Ε','Ε','Ε');
INSERT INTO "customers" VALUES (10,'Ζ','Ζ','Ζ','Ζ');
INSERT INTO "customers" VALUES (12,'Θ','Θ','Θ','Θ');
INSERT INTO "customers" VALUES (14,'Κ','Κ','Κ','Κ');
INSERT INTO "customers" VALUES (15,'Λ','Λ','Λ','Λ');
INSERT INTO "customers" VALUES (16,'Μ','Μ','Μ','Μ');
INSERT INTO "customers" VALUES (17,'Α','Α','Α','Α');
INSERT INTO "customers" VALUES (18,'Β','Β','Β','Β');
INSERT INTO "customers" VALUES (19,'Ι','Ι','Ι','Ι');
INSERT INTO "customers" VALUES (20,'Θεόδωρος','Παπαδόπουλος','1234567890','std168291@ac.eap.gr');
INSERT INTO "customers" VALUES (21,'Σοφοκλής','Παπακωνσταντίνου','0987654321','std168295@ac.eap.gr');
INSERT INTO "customers" VALUES (22,'Can','Dereli','1209387456','candereli@gmail.not');
INSERT INTO "customers" VALUES (23,'Κωνσταντίνος','Λαμόγιος','6937281901','lamogio@gmail.com');
INSERT INTO "customers" VALUES (24,'Απόστολος','Καχριμάνης','6667778889','kahri6789@gmail.not');
INSERT INTO "customers" VALUES (25,'a','a','a','b');
INSERT INTO "customers" VALUES (26,'A','A','A','B');
COMMIT;
