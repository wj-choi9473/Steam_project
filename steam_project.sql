CREATE TABLE "applist" (
  "appid" SERIAL,
  "appname" varchar,
  "alltimepick" int,
  "current" int,
  PRIMARY KEY ("appid", "appname")
);

CREATE TABLE "appinfo" (
  "appid" int,
  "title" varchar,
  "developer" varchar,
  "publisher" varchar,
  "genres" varchar,
  "release_date" datetime,
  "specs" varchar,
  "sys_requirements" varchar,
  "user_tages" varchar
);

CREATE TABLE "appdemand" (
  "appid" int,
  "time" datetime,
  "value" int,
  "values_twitch" int
);

CREATE TABLE "price_sale" (
  "appid" int,
  "time" datetime,
  "price" int,
  "price_us" varchar,
  "discount_rate" int,
  "discount_name" varchar
);

CREATE TABLE "update_history" (
  "appid" int,
  "date" datetime,
  "day" varchar,
  "time" timestamp,
  "patchtitle" varchar,
  "buildid" int
);

CREATE TABLE "metacritic_products" (
  "appname" varchar,
  "num_of_players" varchar,
  "rating" varchar
);

CREATE TABLE "metacritic_user_reviews" (
  "metacritic_name" varchar,
  "username" varchar PRIMARY KEY,
  "date" datetime,
  "rating" varchar,
  "review" varchar
);

CREATE TABLE "metacritic_user_info" (
  "username" varchar,
  "date" datetime,
  "review_product" varchar,
  "rating_score" varchar,
  "average_user_score" varchar
);

ALTER TABLE "appinfo" ADD FOREIGN KEY ("appid") REFERENCES "applist" ("appid");

ALTER TABLE "appdemand" ADD FOREIGN KEY ("appid") REFERENCES "applist" ("appid");

ALTER TABLE "price_sale" ADD FOREIGN KEY ("appid") REFERENCES "applist" ("appid");

ALTER TABLE "update_history" ADD FOREIGN KEY ("appid") REFERENCES "applist" ("appid");

ALTER TABLE "metacritic_products" ADD FOREIGN KEY ("appname") REFERENCES "applist" ("appname");

ALTER TABLE "metacritic_user_reviews" ADD FOREIGN KEY ("metacritic_name") REFERENCES "applist" ("appname");

ALTER TABLE "metacritic_user_reviews" ADD FOREIGN KEY ("metacritic_name") REFERENCES "metacritic_products" ("appname");

ALTER TABLE "metacritic_user_info" ADD FOREIGN KEY ("username") REFERENCES "metacritic_user_reviews" ("username");

