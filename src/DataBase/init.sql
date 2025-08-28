create table user_info(
    id uuid primary key default gen_random_uuid(),
    username varchar(40) not null
);

create table trackinfo(
    trackID varchar(200) primary key,
    trackName varchar(200) not null,
    artistName varchar(100) not null,
    artistID varchar(100) not null,
    releaseDate varchar(100) not null
);

create table songDetails(
    trackID varchar(200),
    trackName varchar(200),
    artistName varchar(100),
    albumName varchar(100),
    releaseDate varchar(100),
    durationMs int,
    popularity int,
    explicit boolean,
    trackNumber int,
    discNumber int,
    previewUrl varchar(200),
    spotifyUrl varchar(200),

    constraint songDetails_trackID_fkey foreign key (trackID) references trackinfo(trackID) on delete cascade,
    constraint songDetails_trackName_fkey foreign key (trackName) references trackinfo(trackName) on delete cascade,
    constraint songDetails_artistName_fkey foreign key (artistName) references trackinfo(artistName) on delete cascade
);

create table artistDetails(
    artistID varchar(200),
    artistName varchar(100),
    genres varchar(200),
    popularity int,
    followers int,
    spotifyUrl varchar(200),

    constraint artistDetails_artistID_fkey foreign key (artistID) references trackinfo(artistID) on delete cascade,
    constraint artistDetails_artistName_fkey foreign key (artistName) references trackinfo(artistName) on delete cascade
);

