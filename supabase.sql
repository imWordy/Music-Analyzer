-- Create genres table
CREATE TABLE public.genres (
  genre_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  genre_name TEXT NOT NULL UNIQUE
);

-- Create directors table
CREATE TABLE public.directors (
  director_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  director_name TEXT NOT NULL
);

-- Create movies table
CREATE TABLE public.movies (
  movie_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  release_year INTEGER NOT NULL,
  genre_id UUID REFERENCES public.genres(genre_id),
  director_id UUID REFERENCES public.directors(director_id),
  poster_url TEXT,
  description TEXT,
  rating_avg DECIMAL(3,1) DEFAULT 0,
  trailer_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create auth.users table
-- This table replaces the original public.users and public.auth tables
-- to follow Supabase conventions and fix inconsistencies.
CREATE TABLE auth.users
(
    id                     UUID PRIMARY KEY         DEFAULT gen_random_uuid(),
    instance_id            UUID,
    aud                    VARCHAR(255),
    role                   VARCHAR(255),
    email                  VARCHAR(255) UNIQUE,
    encrypted_password     VARCHAR(255),
    email_confirmed_at     TIMESTAMP WITH TIME ZONE,
    invited_at             TIMESTAMP WITH TIME ZONE,
    confirmation_token     VARCHAR(255),
    confirmation_sent_at   TIMESTAMP WITH TIME ZONE,
    recovery_token         VARCHAR(255),
    recovery_sent_at       TIMESTAMP WITH TIME ZONE,
    email_change_token_new VARCHAR(255),
    email_change           VARCHAR(255),
    email_change_sent_at   TIMESTAMP WITH TIME ZONE,
    last_sign_in_at        TIMESTAMP WITH TIME ZONE,
    raw_app_meta_data      JSONB,
    raw_user_meta_data     JSONB,
    is_super_admin         BOOLEAN,
    created_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT proper_email CHECK (email ~* '^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$')
);

-- Create user profiles table
-- References auth.users instead of a separate public.users table
CREATE TABLE public.profiles (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create ratings table
CREATE TABLE public.ratings (
  rating_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(user_id) ON DELETE CASCADE,
  movie_id UUID REFERENCES public.movies(movie_id) ON DELETE CASCADE,
  rating_value INTEGER CHECK (rating_value >= 1 AND rating_value <= 5),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, movie_id)
);

-- Create watchlist table
CREATE TABLE public.watchlist (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(user_id) ON DELETE CASCADE,
  movie_id UUID REFERENCES public.movies(movie_id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, movie_id)
);

-- Create favorites table
CREATE TABLE public.favorites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(user_id) ON DELETE CASCADE,
  movie_id UUID REFERENCES public.movies(movie_id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, movie_id)
);

-- Enable Row Level Security
ALTER TABLE public.genres ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.directors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;

-- RLS Policies for genres (public read)
CREATE POLICY "Genres are viewable by everyone"
  ON public.genres FOR SELECT
  USING (true);

-- RLS Policies for directors (public read)
CREATE POLICY "Directors are viewable by everyone"
  ON public.directors FOR SELECT
  USING (true);

-- RLS Policies for movies (public read)
CREATE POLICY "Movies are viewable by everyone"
  ON public.movies FOR SELECT
  USING (true);

-- RLS Policies for profiles
CREATE POLICY "Profiles are viewable by everyone"
  ON public.profiles FOR SELECT
  USING (true);

-- RLS Policies for ratings
CREATE POLICY "Ratings are viewable by everyone"
  ON public.ratings FOR SELECT
  USING (true);

-- Trigger to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (user_id, username)
  VALUES (new.id, COALESCE(new.raw_user_meta_data->>'username', split_part(new.email, '@', 1)));
  RETURN new;
END;
$$;

-- The trigger is now on auth.users, which is correct
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update movie rating average
CREATE OR REPLACE FUNCTION public.update_movie_rating()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE public.movies
  SET rating_avg = (
    SELECT COALESCE(AVG(rating_value), 0)
    FROM public.ratings
    WHERE movie_id = COALESCE(NEW.movie_id, OLD.movie_id)
  )
  WHERE movie_id = COALESCE(NEW.movie_id, OLD.movie_id);
  RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER update_movie_rating_trigger
  AFTER INSERT OR UPDATE OR DELETE ON public.ratings
  FOR EACH ROW EXECUTE FUNCTION public.update_movie_rating();

-- Insert sample genres
INSERT INTO public.genres (genre_name) VALUES
  ('Action'),
  ('Drama'),
  ('Comedy'),
  ('Sci-Fi'),
  ('Horror'),
  ('Romance'),
  ('Thriller'),
  ('Animation'),
  ('Documentary'),
  ('Fantasy');

-- Insert sample directors
INSERT INTO public.directors (director_name) VALUES
  ('Christopher Nolan'),
  ('Greta Gerwig'),
  ('Denis Villeneuve'),
  ('Wes Anderson'),
  ('Jordan Peele'),
  ('Hayao Miyazaki'),
  ('Taika Waititi'),
  ('Bong Joon-ho');

-- Insert sample movies
INSERT INTO public.movies (title, release_year, genre_id, director_id, poster_url, description, trailer_url)
SELECT
  'Interstellar',
  2014,
  (SELECT genre_id FROM public.genres WHERE genre_name = 'Sci-Fi'),
  (SELECT director_id FROM public.directors WHERE director_name = 'Christopher Nolan'),
  'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400',
  'A team of explorers travel through a wormhole in space in an attempt to ensure humanity''s survival.',
  'https://www.youtube.com/embed/zSWdZVtXT7E'
UNION ALL SELECT
  'Barbie',
  2023,
  (SELECT genre_id FROM public.genres WHERE genre_name = 'Comedy'),
  (SELECT director_id FROM public.directors WHERE director_name = 'Greta Gerwig'),
  'https://images.unsplash.com/photo-1594908900066-3f47337549d8?w=400',
  'Barbie and Ken are having the time of their lives in the colorful and seemingly perfect world of Barbie Land.',
  'https://www.youtube.com/embed/pBk4NYhWNMM'
UNION ALL SELECT
  'Dune',
  2021,
  (SELECT genre_id FROM public.genres WHERE genre_name = 'Sci-Fi'),
  (SELECT director_id FROM public.directors WHERE director_name = 'Denis Villeneuve'),
  'https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?w=400',
  'Paul Atreides arrives on Arrakis after his father accepts the stewardship of the dangerous planet.',
  'https://www.youtube.com/embed/8g18jFHCLXk'
UNION ALL SELECT
  'The Grand Budapest Hotel',
  2014,
  (SELECT genre_id FROM public.genres WHERE genre_name = 'Comedy'),
  (SELECT director_id FROM public.directors WHERE director_name = 'Wes Anderson'),
  'https://images.unsplash.com/photo-1598899134739-24c46f58b8c0?w=400',
  'A writer encounters the owner of an aging high-class hotel, who tells him of his early years.',
  'https://www.youtube.com/embed/1Fg5iWmQjwk'
UNION ALL SELECT
  'Get Out',
  2017,
  (SELECT genre_id FROM public.genres WHERE genre_name = 'Horror'),
  (SELECT director_id FROM public.directors WHERE director_name = 'Jordan Peele'),
  'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400',
  'A young African-American visits his white girlfriend''s parents, uncovering a disturbing secret.',
  'https://www.youtube.com/embed/DzfpyUB60YY'
UNION ALL SELECT
  'Spirited Away',
  2001,
  (SELECT genre_id FROM public.genres WHERE genre_name = 'Animation'),
  (SELECT director_id FROM public.directors WHERE director_name = 'Hayao Miyazaki'),
  'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=400',
  'During her family''s move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods and witches.',
  'https://www.youtube.com/embed/ByXuk9QqQkk';