CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'entrenador', 'atleta') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE atletas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    entrenador_id INT NOT NULL,

    fecha_nacimiento DATE,
    sexo ENUM('M', 'F', 'O'),
    altura_cm INT,
    peso_kg DECIMAL(5,2),

    experiencia_anios INT,
    dias_entreno_semana INT,

    volumen_actual_km DECIMAL(6,2),
    vam DECIMAL(4,2),
    ritmo_umbral INT, -- segundos por km

    categoria VARCHAR(50),

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (entrenador_id) REFERENCES usuarios(id)
);
CREATE TABLE plantillas_plan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    distancia_objetivo VARCHAR(20),
    nivel ENUM('base', 'intermedio', 'avanzado'),
    duracion_semanas INT,
    metodo VARCHAR(50)
);
CREATE TABLE plantillas_sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plantilla_id INT NOT NULL,
    semana INT NOT NULL,
    dia_semana INT NOT NULL, -- 1=Lunes ... 7=Domingo

    tipo_sesion VARCHAR(50),
    volumen_base DECIMAL(6,2),
    intensidad_pct_vam DECIMAL(5,2),
    formato_series VARCHAR(100),
    recuperacion_seg INT,

    FOREIGN KEY (plantilla_id) REFERENCES plantillas_plan(id)
);
CREATE TABLE planes_atleta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    atleta_id INT NOT NULL,
    plantilla_id INT NOT NULL,

    fecha_inicio DATE,
    fecha_fin DATE,
    objetivo_descripcion TEXT,

    estado ENUM('activo', 'completado', 'cancelado') DEFAULT 'activo',

    FOREIGN KEY (atleta_id) REFERENCES atletas(id),
    FOREIGN KEY (plantilla_id) REFERENCES plantillas_plan(id)
);
CREATE TABLE entrenamientos_planificados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id INT NOT NULL,
    fecha DATE NOT NULL,

    tipo_sesion VARCHAR(50),
    volumen_objetivo DECIMAL(6,2),
    ritmo_objetivo INT, -- segundos por km
    detalle_series VARCHAR(150),

    comentarios_entrenador TEXT,
    realizado_id INT,

    FOREIGN KEY (plan_id) REFERENCES planes_atleta(id),
    FOREIGN KEY (realizado_id) REFERENCES entrenamientos_realizados(id)
);
CREATE TABLE entrenamientos_realizados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    atleta_id INT NOT NULL,
    fecha DATE NOT NULL,

    origen ENUM('manual', 'strava', 'garmin', 'polar'),
    tipo_sesion VARCHAR(20),
    actividad_id_externa VARCHAR(100),

    distancia_km DECIMAL(6,2),
    tiempo_seg INT,
    ritmo_medio INT,
    fc_media INT,
    fc_max INT,
    desnivel_m INT,

    sensacion INT, -- escala 1-10
    comentarios TEXT,
    planificado_id INT,
    match_confianza DECIMAL(4,2),
    match_metodo VARCHAR(20),

    FOREIGN KEY (atleta_id) REFERENCES atletas(id),
    FOREIGN KEY (planificado_id) REFERENCES entrenamientos_planificados(id)
);
CREATE TABLE comparacion_plan_real (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id INT,
    atleta_id INT,
    fecha DATE,
    entrenamiento_planificado_id INT NOT NULL,
    entrenamiento_realizado_id INT NOT NULL,

    dist_plan_km DECIMAL(6,2),
    dist_real_km DECIMAL(6,2),
    pct_dist DECIMAL(5,2),

    ritmo_plan INT,
    ritmo_real INT,
    delta_ritmo INT,

    sensacion INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    cumplimiento_pct DECIMAL(5,2),
    desviacion_volumen DECIMAL(6,2),
    desviacion_ritmo INT,

    estado ENUM('ok', 'ajustado', 'fallido'),

    FOREIGN KEY (plan_id) REFERENCES planes_atleta(id),
    FOREIGN KEY (atleta_id) REFERENCES atletas(id),
    FOREIGN KEY (entrenamiento_planificado_id)
        REFERENCES entrenamientos_planificados(id),
    FOREIGN KEY (entrenamiento_realizado_id)
        REFERENCES entrenamientos_realizados(id)
);
CREATE TABLE metricas_atleta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    atleta_id INT NOT NULL,
    fecha DATE NOT NULL,

    carga_semanal DECIMAL(6,2),
    fatiga_estimada DECIMAL(5,2),
    tendencia_rendimiento DECIMAL(5,2),
    riesgo_lesion DECIMAL(5,2),

    FOREIGN KEY (atleta_id) REFERENCES atletas(id)
);
CREATE TABLE recomendaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    atleta_id INT NOT NULL,
    fecha DATE NOT NULL,

    tipo VARCHAR(50),
    descripcion TEXT,
    nivel_confianza DECIMAL(4,2),

    aplicada BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (atleta_id) REFERENCES atletas(id)
);
CREATE TABLE coach_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id INT NOT NULL,
    semana VARCHAR(10),
    fecha DATE,
    tipo ENUM('semanal', 'diaria', 'reversion') NOT NULL,
    acciones JSON NOT NULL,
    estado ENUM('aplicada', 'revertida') DEFAULT 'aplicada',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (plan_id) REFERENCES planes_atleta(id)
);
