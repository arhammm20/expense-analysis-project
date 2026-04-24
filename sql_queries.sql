CREATE DATABASE expense_db;
USE expense_db;


SELECT * FROM transactions LIMIT 10;
SELECT SUM(Amount) from transactions where Type='Debit';
SELECT SUM(Amount) from transactions where Type='Credit';


SELECT Category, SUM(Amount) AS total_spend
FROM transactions
WHERE Type = 'Debit'
GROUP BY Category
ORDER BY total_spend DESC;


SELECT Month, SUM(Amount) AS total_spend
FROM transactions
WHERE Type = 'Debit'
GROUP BY Month
ORDER BY Month;

SELECT *
FROM transactions
WHERE Type = 'Debit'
ORDER BY Amount DESC
LIMIT 5;