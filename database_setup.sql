-- Database schema for Game Directory Project
CREATE TABLE Developers (
    DeveloperID SERIAL PRIMARY KEY,
    DeveloperName VARCHAR(100) NOT NULL,
    Country VARCHAR(50)
);

CREATE TABLE Publishers (
    PublisherID SERIAL PRIMARY KEY,
    PublisherName VARCHAR(100) NOT NULL,
    Country VARCHAR(50)
);

CREATE TABLE Platforms (
    PlatformID SERIAL PRIMARY KEY,
    PlatformName VARCHAR(50) NOT NULL,
    ReleaseYear INT
);

CREATE TABLE Genres (
    GenreID SERIAL PRIMARY KEY,
    GenreName VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Games (
    GameID SERIAL PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    ReleaseYear INT,
    DeveloperID INT REFERENCES Developers(DeveloperID),
    PublisherID INT REFERENCES Publishers(PublisherID),
    PlatformID INT REFERENCES Platforms(PlatformID),
    GenreID INT REFERENCES Genres(GenreID),
    MetacriticScore DECIMAL(3,1),
    UserScore DECIMAL(3,1),
    GlobalSales DECIMAL(10,2)
);

-- Sample seed data
INSERT INTO Developers (DeveloperName, Country) VALUES 
('Rockstar Games', 'USA'),
('CD Projekt Red', 'Poland'),
('Nintendo EPD', 'Japan');

INSERT INTO Publishers (PublisherName, Country) VALUES 
('Rockstar Games', 'USA'),
('CD Projekt', 'Poland'),
('Nintendo', 'Japan');

INSERT INTO Platforms (PlatformName, ReleaseYear) VALUES 
('PlayStation 5', 2020),
('Nintendo Switch', 2017),
('PC', NULL);

INSERT INTO Genres (GenreName) VALUES 
('Action-Adventure'),
('Role-Playing'),
('Platformer');

INSERT INTO Games (Title, ReleaseYear, DeveloperID, PublisherID, PlatformID, GenreID, MetacriticScore, UserScore, GlobalSales) VALUES
('Red Dead Redemption 2', 2018, 1, 1, 1, 1, 97, 8.5, 45.0),
('The Witcher 3: Wild Hunt', 2015, 2, 2, 3, 2, 93, 9.2, 50.0),
('Super Mario Odyssey', 2017, 3, 3, 2, 3, 97, 8.9, 25.0);