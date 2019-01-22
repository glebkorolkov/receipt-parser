-- Change database
use receipt_labeler;

-- Disable foreign key checks
set foreign_key_checks=0;

-- Load receipts
TRUNCATE table labeler_receipt;

load data local infile "/path/to/project/data/receipts.csv"
into table labeler_receipt
fields terminated by ',' enclosed by '"'
lines terminated by '\n'
ignore 1 lines;

update labeler_receipt set date_add=now() where 1;

-- Load words
TRUNCATE table labeler_word;

load data local infile "/path/to/project/data/words.csv"
into table labeler_word
fields terminated by ',' enclosed by '"'
lines terminated by '\n'
ignore 1 lines;

update labeler_word set date_add=now() where 1;

-- Enable foreign key checks
set foreign_key_checks=1;
