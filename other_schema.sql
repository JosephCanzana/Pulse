USE lms_db;

-- ✅ TABLE CREATION
CREATE TABLE IF NOT EXISTS motivational_quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote TEXT NOT NULL,
    author VARCHAR(100),
    category VARCHAR(50),
    is_featured BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grateful_peace_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    theme ENUM('Grateful', 'Peace') NOT NULL,
    source VARCHAR(100),
    is_featured BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bible_verses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    verse_text TEXT NOT NULL,
    reference VARCHAR(50),
    topic VARCHAR(50),
    is_featured BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_inspirations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_id INT,
    verse_id INT,
    message_id INT,
    date DATE UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ✅ INSERT 30 MOTIVATIONAL QUOTES
INSERT INTO motivational_quotes (quote, author, category, is_featured, created_by)
VALUES
('The future belongs to those who believe in the beauty of their dreams.', 'Eleanor Roosevelt', 'Inspiration', TRUE, 'admin'),
('Don’t watch the clock; do what it does. Keep going.', 'Sam Levenson', 'Perseverance', FALSE, 'admin'),
('Success is not final, failure is not fatal: it is the courage to continue that counts.', 'Winston Churchill', 'Courage', TRUE, 'admin'),
('Start where you are. Use what you have. Do what you can.', 'Arthur Ashe', 'Action', FALSE, 'admin'),
('Dream big and dare to fail.', 'Norman Vaughan', 'Dreams', FALSE, 'admin'),
('What we think, we become.', 'Buddha', 'Mindset', FALSE, 'admin'),
('Do something today that your future self will thank you for.', 'Unknown', 'Growth', FALSE, 'admin'),
('Believe you can and you’re halfway there.', 'Theodore Roosevelt', 'Confidence', TRUE, 'admin'),
('It always seems impossible until it’s done.', 'Nelson Mandela', 'Determination', FALSE, 'admin'),
('Hard work beats talent when talent doesn’t work hard.', 'Tim Notke', 'Hard Work', FALSE, 'admin'),
('Push yourself, because no one else is going to do it for you.', 'Unknown', 'Self-Discipline', FALSE, 'admin'),
('Great things never come from comfort zones.', 'Unknown', 'Courage', FALSE, 'admin'),
('The harder you work for something, the greater you’ll feel when you achieve it.', 'Unknown', 'Hard Work', FALSE, 'admin'),
('Success doesn’t just find you. You have to go out and get it.', 'Unknown', 'Success', TRUE, 'admin'),
('Small progress is still progress.', 'Unknown', 'Persistence', FALSE, 'admin'),
('Don’t stop until you’re proud.', 'Unknown', 'Motivation', TRUE, 'admin'),
('You are never too old to set another goal or to dream a new dream.', 'C.S. Lewis', 'Inspiration', FALSE, 'admin'),
('Doubt kills more dreams than failure ever will.', 'Suzy Kassem', 'Mindset', FALSE, 'admin'),
('Discipline is the bridge between goals and accomplishment.', 'Jim Rohn', 'Discipline', FALSE, 'admin'),
('Don’t let yesterday take up too much of today.', 'Will Rogers', 'Positivity', FALSE, 'admin'),
('Your limitation—it’s only your imagination.', 'Unknown', 'Mindset', FALSE, 'admin'),
('Sometimes later becomes never. Do it now.', 'Unknown', 'Action', FALSE, 'admin'),
('Work hard in silence, let success make the noise.', 'Frank Ocean', 'Success', FALSE, 'admin'),
('Don’t wish it were easier. Wish you were better.', 'Jim Rohn', 'Self-Improvement', TRUE, 'admin'),
('Everything you’ve ever wanted is on the other side of fear.', 'George Addair', 'Courage', FALSE, 'admin'),
('Opportunities don’t happen. You create them.', 'Chris Grosser', 'Action', FALSE, 'admin'),
('Failure is simply the opportunity to begin again, this time more intelligently.', 'Henry Ford', 'Resilience', FALSE, 'admin'),
('Act as if what you do makes a difference. It does.', 'William James', 'Purpose', FALSE, 'admin'),
('You don’t have to be great to start, but you have to start to be great.', 'Zig Ziglar', 'Starting', FALSE, 'admin'),
('Learn as if you will live forever, live like you will die tomorrow.', 'Mahatma Gandhi', 'Learning', TRUE, 'admin');

-- ✅ INSERT 30 BIBLE VERSES
INSERT INTO bible_verses (verse_text, reference, topic, is_featured, created_by)
VALUES
('I can do all things through Christ who strengthens me.', 'Philippians 4:13', 'Strength', TRUE, 'admin'),
('For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you.', 'Jeremiah 29:11', 'Hope', TRUE, 'admin'),
('The Lord is my shepherd; I shall not want.', 'Psalm 23:1', 'Faith', FALSE, 'admin'),
('Trust in the Lord with all your heart and lean not on your own understanding.', 'Proverbs 3:5', 'Trust', TRUE, 'admin'),
('Be strong and courageous. Do not be afraid; for the Lord your God goes with you.', 'Deuteronomy 31:6', 'Courage', FALSE, 'admin'),
('The fear of the Lord is the beginning of wisdom.', 'Proverbs 9:10', 'Wisdom', FALSE, 'admin'),
('The Lord will fight for you; you need only to be still.', 'Exodus 14:14', 'Peace', FALSE, 'admin'),
('Let all that you do be done in love.', '1 Corinthians 16:14', 'Love', TRUE, 'admin'),
('Cast all your anxiety on Him because He cares for you.', '1 Peter 5:7', 'Comfort', FALSE, 'admin'),
('With God all things are possible.', 'Matthew 19:26', 'Faith', FALSE, 'admin'),
('The Lord is my light and my salvation—whom shall I fear?', 'Psalm 27:1', 'Courage', FALSE, 'admin'),
('Commit to the Lord whatever you do, and He will establish your plans.', 'Proverbs 16:3', 'Guidance', FALSE, 'admin'),
('Blessed are the peacemakers, for they will be called children of God.', 'Matthew 5:9', 'Peace', FALSE, 'admin'),
('Rejoice always, pray continually, give thanks in all circumstances.', '1 Thessalonians 5:16-18', 'Gratitude', FALSE, 'admin'),
('Do not be conformed to this world, but be transformed by the renewal of your mind.', 'Romans 12:2', 'Renewal', FALSE, 'admin'),
('The Lord is near to the brokenhearted and saves the crushed in spirit.', 'Psalm 34:18', 'Comfort', TRUE, 'admin'),
('In everything give thanks; for this is the will of God in Christ Jesus.', '1 Thessalonians 5:18', 'Gratitude', FALSE, 'admin'),
('My grace is sufficient for you, for my power is made perfect in weakness.', '2 Corinthians 12:9', 'Grace', FALSE, 'admin'),
('Your word is a lamp to my feet and a light to my path.', 'Psalm 119:105', 'Guidance', FALSE, 'admin'),
('The steadfast love of the Lord never ceases; His mercies never come to an end.', 'Lamentations 3:22-23', 'Love', TRUE, 'admin'),
('Seek first the kingdom of God and His righteousness.', 'Matthew 6:33', 'Faith', FALSE, 'admin'),
('Be still, and know that I am God.', 'Psalm 46:10', 'Peace', FALSE, 'admin'),
('If God is for us, who can be against us?', 'Romans 8:31', 'Faith', TRUE, 'admin'),
('The Lord is good, a refuge in times of trouble.', 'Nahum 1:7', 'Protection', FALSE, 'admin'),
('Let your light shine before others.', 'Matthew 5:16', 'Purpose', FALSE, 'admin'),
('Do everything in love.', '1 Corinthians 16:14', 'Love', FALSE, 'admin'),
('Whatever you do, work at it with all your heart, as working for the Lord.', 'Colossians 3:23', 'Work', FALSE, 'admin'),
('The joy of the Lord is your strength.', 'Nehemiah 8:10', 'Joy', TRUE, 'admin'),
('Ask, and it will be given to you; seek, and you will find.', 'Matthew 7:7', 'Prayer', FALSE, 'admin'),
('For God so loved the world that He gave His one and only Son.', 'John 3:16', 'Salvation', TRUE, 'admin');


INSERT INTO grateful_peace_messages (message, theme, source, is_featured, created_by)
VALUES
-- 🌿 Grateful Messages
('Gratitude turns what we have into enough.', 'Grateful', 'Anonymous', TRUE, 'admin'),
('Be thankful for the small things, the big things, and everything in between.', 'Grateful', 'Unknown', FALSE, 'admin'),
('A grateful heart is a magnet for miracles.', 'Grateful', 'Unknown', TRUE, 'admin'),
('Gratitude unlocks the fullness of life.', 'Grateful', 'Melody Beattie', FALSE, 'admin'),
('When we focus on our gratitude, the tide of disappointment goes out.', 'Grateful', 'Unknown', FALSE, 'admin'),
('Every day may not be good, but there is something good in every day.', 'Grateful', 'Alice Morse Earle', FALSE, 'admin'),
('Give thanks not because life is perfect, but because it is a gift.', 'Grateful', 'Unknown', TRUE, 'admin'),
('The more grateful you are, the more beauty you see.', 'Grateful', 'Mary Davis', FALSE, 'admin'),
('Gratitude is the fairest blossom that springs from the soul.', 'Grateful', 'Henry Ward Beecher', FALSE, 'admin'),
('A thankful heart is a happy heart.', 'Grateful', 'Unknown', FALSE, 'admin'),
('Count your blessings and your problems will seem smaller.', 'Grateful', 'Unknown', FALSE, 'admin'),
('Gratitude turns pain into healing, and chaos into order.', 'Grateful', 'Melody Beattie', TRUE, 'admin'),
('Start each day with a grateful heart.', 'Grateful', 'Unknown', TRUE, 'admin'),
('Appreciate what you have before it becomes what you had.', 'Grateful', 'Unknown', FALSE, 'admin'),
('In the midst of change, be thankful for what remains.', 'Grateful', 'Unknown', FALSE, 'admin'),

-- 🌸 Peace Messages
('Peace begins with a smile.', 'Peace', 'Mother Teresa', TRUE, 'admin'),
('When the world is at war, let your heart be still.', 'Peace', 'Unknown', FALSE, 'admin'),
('Do not let the behavior of others destroy your inner peace.', 'Peace', 'Dalai Lama', TRUE, 'admin'),
('Peace is not the absence of trouble, but the presence of Christ.', 'Peace', 'Unknown', TRUE, 'admin'),
('You will keep in perfect peace those whose minds are steadfast.', 'Peace', 'Isaiah 26:3', FALSE, 'admin'),
('The more you practice peace, the stronger it becomes.', 'Peace', 'Unknown', FALSE, 'admin'),
('Peace does not mean to be in a place where there is no noise or trouble, but to remain calm in the midst of it.', 'Peace', 'Unknown', FALSE, 'admin'),
('Calm mind brings inner strength and self-confidence.', 'Peace', 'Dalai Lama', FALSE, 'admin'),
('Let the peace of God rule in your hearts.', 'Peace', 'Colossians 3:15', TRUE, 'admin'),
('Within you, there is a stillness and a sanctuary to which you can retreat.', 'Peace', 'Hermann Hesse', FALSE, 'admin'),
('Find peace in the moment, not in the outcome.', 'Peace', 'Unknown', FALSE, 'admin'),
('Peace cannot be kept by force; it can only be achieved by understanding.', 'Peace', 'Albert Einstein', TRUE, 'admin'),
('Peace is the result of retraining your mind to process life as it is.', 'Peace', 'Wayne Dyer', FALSE, 'admin'),
('The quieter you become, the more you hear.', 'Peace', 'Ram Dass', FALSE, 'admin'),
('Where there is peace, there is power.', 'Peace', 'Unknown', FALSE, 'admin');