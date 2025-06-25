import { IUserRepository } from '../services/interfaces';
import { User, UserDocument } from '../models/user_model';

export class MongoUserRepository implements IUserRepository {
  async findById(id: string): Promise<UserDocument | null> {
    return User.findById(id);
  }

  async findByEmail(email: string): Promise<UserDocument | null> {
    return User.findOne({ email });
  }

  async create(data: Partial<UserDocument>): Promise<UserDocument> {
    return User.create(data);
  }

  async update(id: string, data: Partial<UserDocument>): Promise<UserDocument> {
    const user = await User.findByIdAndUpdate(id, data, { new: true });
    if (!user) {
      throw new Error(`User with ID ${id} not found`);
    }
    return user;
  }

  async updatePassword(id: string, hashedPassword: string): Promise<UserDocument> {
    const user = await User.findByIdAndUpdate(
      id,
      { password: hashedPassword },
      { new: true }
    );
    if (!user) {
      throw new Error(`User with ID ${id} not found`);
    }
    return user;
  }

  async updatePreferences(id: string, preferences: any): Promise<UserDocument> {
    const user = await User.findByIdAndUpdate(
      id,
      { $set: { preferences } },
      { new: true }
    );
    if (!user) {
      throw new Error(`User with ID ${id} not found`);
    }
    return user;
  }

  async delete(id: string): Promise<boolean> {
    const result = await User.findByIdAndDelete(id);
    return result !== null;
  }

  getUserModel() {
    return User;
  }
} 