import { generateHash } from '../utils/password';

const password = 'admin123';

generateHash(password).then(hash => {
  console.log('Generated hash:', hash);
}); 