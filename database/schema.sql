CREATE TABLE IF NOT EXISTS agronomists (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    phone       VARCHAR(20),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS farms (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    agronomist_id   INT NOT NULL,
    name            VARCHAR(100) NOT NULL,
    location        VARCHAR(255),
    area_hectares   NUMERIC(10, 2),
    crop_type       VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW(),
    soil_type       VARCHAR(100),
    field_capacity_pct NUMERIC(5, 2),
    wilting_point_pct NUMERIC(5, 2),
    growth_stage    VARCHAR(50),
    FOREIGN KEY (agronomist_id) REFERENCES agronomists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS soil_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farm_id INT NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    moisture_pct NUMERIC(5, 2),
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE

);

CREATE TABLE IF NOT EXISTS weather_readings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    farm_id         INT NOT NULL,
    recorded_at     TIMESTAMP NOT NULL,
    location        VARCHAR(255),
    temperature_c   NUMERIC(5, 2),
    description     VARCHAR(255),
    humidity_pct    NUMERIC(5, 2),
    rainfall_mm     NUMERIC(8, 2),
    wind_speed_kph  NUMERIC(6, 2),
    et0_mm          NUMERIC(8, 2),  -- reference evapotranspiration
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS irrigation_recommendations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    farm_id         INT NOT NULL,
    weather_id      INT,
    recommended_at  TIMESTAMP DEFAULT NOW(),
    water_amount_mm NUMERIC(8, 2) NOT NULL,
    duration_hours  NUMERIC(5, 2),
    method          VARCHAR(50),   -- e.g. drip, sprinkler, flood
    notes           TEXT,
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, applied, skipped
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE,
    FOREIGN KEY (weather_id) REFERENCES weather_readings(id) ON DELETE SET NULL
);
