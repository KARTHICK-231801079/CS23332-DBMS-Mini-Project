
USE carbon_emission;

-- Table to store user information and emission data
CREATE TABLE emissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    electricity DOUBLE NOT NULL,
    petrol DOUBLE NOT NULL,
    diesel DOUBLE NOT NULL,
    wastewater DOUBLE NOT NULL,
    gas DOUBLE NOT NULL,
    total_emission DOUBLE NOT NULL,
    emission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
