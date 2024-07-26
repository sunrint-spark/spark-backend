db = db.getSiblingDB('spark');
db.createUser({
  user: 'root',
  pwd: 'password',
  roles: [{ role: 'readWrite', db: 'spark' }]
});