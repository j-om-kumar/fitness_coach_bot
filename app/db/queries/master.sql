-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    chat_id BIGINT NOT NULL,
    timezone VARCHAR(64) DEFAULT 'Asia/Kolkata',
    
    -- Registration/Onboarding fields
    registration_completed INTEGER DEFAULT 0 NOT NULL,
    height_cm NUMERIC(5, 2),
    initial_weight_kg NUMERIC(5, 2),
    target_weight_kg NUMERIC(5, 2),
    goal VARCHAR(64),
    activity_level VARCHAR(32),
    
    -- Daily nutrition targets
    daily_calorie_target INTEGER,
    daily_protein_target INTEGER,
    daily_carbs_target INTEGER,
    daily_fats_target INTEGER,
    daily_fiber_target INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Daily Logs Table
CREATE TABLE IF NOT EXISTS daily_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE DEFAULT CURRENT_DATE NOT NULL,
    
    weight_kg NUMERIC(5, 2),
    steps INTEGER,
    
    -- Photo tracking
    body_photo_file_id TEXT,
    weight_scale_photo_file_id TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: One log per user per day
    UNIQUE(user_id, log_date)
);

-- 3. Meals Table
CREATE TABLE IF NOT EXISTS meals (
    id SERIAL PRIMARY KEY,
    daily_log_id INTEGER NOT NULL REFERENCES daily_logs(id) ON DELETE CASCADE,
    
    meal_type VARCHAR(16) NOT NULL,
    description TEXT,
    
    -- Nutritional information
    calories_kcal INTEGER,
    protein_g INTEGER,
    carbs_g INTEGER,
    fats_g INTEGER,
    fiber_g INTEGER,
    
    photo_file_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date ON daily_logs(user_id, log_date);
CREATE INDEX IF NOT EXISTS idx_meals_daily_log_id ON meals(daily_log_id);