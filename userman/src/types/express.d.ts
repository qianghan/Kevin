import { UserDocument } from '../models/user_model';

declare global {
  namespace Express {
    interface Request {
      user?: UserDocument;
      serviceEntitlement?: any;
    }
  }
}

export {}; 