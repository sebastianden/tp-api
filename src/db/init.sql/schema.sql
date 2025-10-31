-- Initialize the database with the normalized tables

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100)
);

-- Create businesses table
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Create reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    business_id UUID NOT NULL REFERENCES businesses(id),
    title VARCHAR(255),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    content TEXT,
    ip_address INET,
    date TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_business_id ON reviews(business_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date);

-- Create a view for denormalized data (for reporting)
CREATE OR REPLACE VIEW review_details AS
SELECT
    r.id as review_id,
    r.user_id,
    r.business_id,
    u.name as user_name,
    u.email as user_email,
    u.country as user_country,
    b.name as business_name,
    r.title as review_title,
    r.rating as review_rating,
    r.content as review_content,
    r.ip_address as review_ip_address,
    r.date as review_date
FROM reviews r
JOIN users u ON r.user_id = u.id
JOIN businesses b ON r.business_id = b.id
ORDER BY r.date DESC;
