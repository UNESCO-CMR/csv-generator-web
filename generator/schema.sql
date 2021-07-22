DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS generated_files;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  password TEXT NOT NULL,
  status	BOOLEAN DEFAULT 0,
  created_on	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  role	TEXT DEFAULT 'editor'
);


CREATE TABLE regions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  abbr TEXT NOT NULL,
  user_id	INTEGER NOT NULL,
  created_on	TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE files (
	id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	title	VARCHAR NOT NULL UNIQUE,
	path	VARCHAR NOT NULL,
	filename	VARCHAR NOT NULL,
	region_id	INTEGER NOT NULL,
	user_id	INTEGER NOT NULL,
	created_on	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	status	INTEGER DEFAULT -1
);

CREATE TABLE cleaned_files (
	id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	title	VARCHAR NOT NULL UNIQUE,
	path	VARCHAR NOT NULL,
	filename	VARCHAR NOT NULL,
	file_id	INTEGER NOT NULL UNIQUE,
	user_id	INTEGER NOT NULL,
	created_on	TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE file_statuses (
    id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	file_id	INTEGER NOT NULL,
	user_id	INTEGER NOT NULL,
	'from'	INTEGER NOT NULL,
	'to'	INTEGER NOT NULL,
	created_on	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
)


CREATE TABLE generated_files (
	id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	title	VARCHAR NOT NULL UNIQUE,
	path	VARCHAR NOT NULL,
	file_id	INTEGER NOT NULL,
	user_id	INTEGER NOT NULL,
	created_on	TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

